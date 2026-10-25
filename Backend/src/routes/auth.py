import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.Users import User
from src.dependencies import get_current_user, oauth2_scheme
from src.utils.hashing import hash_password, verify_password
from src.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token
)
from src.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    GuestLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

def _build_token_response(user: User) -> TokenResponse:
    token_claims = {
        "sub": user.username,
        "user_id": user.user_id,
        "email": user.email or "",
        "role": user.role,
        "tenant_id": user.tenant_id,
        "is_guest": user.is_guest
    }
    access_token = create_access_token(data=token_claims)
    refresh_token = create_refresh_token(data=token_claims)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        fullname=user.fullname,
        role=user.role,
        tenant_id=user.tenant_id,
        is_guest=user.is_guest,
        expires_in=7200
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account with tenant isolation and role allocation."""
    existing_username = db.query(User).filter(User.username == payload.username.strip().lower()).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )

    existing_email = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    user_id = f"USR{uuid.uuid4().hex[:8].upper()}"
    new_user = User(
        user_id=user_id,
        username=payload.username.strip().lower(),
        fullname=payload.fullname.strip(),
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        mobile_number=payload.mobile_number,
        role=payload.role if payload.role else "Customer",
        tenant_id=payload.tenant_id.strip() if payload.tenant_id else "default",
        is_guest=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User '{new_user.username}' registered successfully (Role: {new_user.role}, Tenant: {new_user.tenant_id})")
    return _build_token_response(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate with username & password (supports JSON body or OAuth2 form-urlencoded)."""
    username = None
    password = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    else:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )

    clean_username = username.strip().lower()
    user = db.query(User).filter(User.username == clean_username).first()

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        logger.warning(f"Login failed: invalid credentials for '{username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check guest expiration if applicable
    if user.is_guest and user.expires_at:
        now = datetime.now(timezone.utc)
        expires_at = user.expires_at if user.expires_at.tzinfo else user.expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Temporary guest session has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

    logger.info(f"User '{user.username}' logged in successfully")
    return _build_token_response(user)


@router.post("/guest", response_model=TokenResponse)
def create_guest_session(
    payload: Optional[GuestLoginRequest] = None,
    db: Session = Depends(get_db)
):
    """Issue a temporary guest session token with a 24-hour TTL."""
    guest_uuid = uuid.uuid4().hex[:8]
    user_id = f"GST{guest_uuid.upper()}"
    username = f"guest_{guest_uuid}"
    fullname = payload.fullname if (payload and payload.fullname) else f"Guest {guest_uuid}"
    tenant_id = payload.tenant_id if (payload and payload.tenant_id) else "default"

    ttl_expiry = datetime.now(timezone.utc) + timedelta(hours=24)

    guest_user = User(
        user_id=user_id,
        username=username,
        fullname=fullname,
        email=f"{username}@guest.temporary",
        password_hash=hash_password(uuid.uuid4().hex),
        role="Customer",
        tenant_id=tenant_id,
        is_guest=True,
        expires_at=ttl_expiry
    )

    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)

    logger.info(f"Guest session created: {guest_user.username} (TTL expires: {ttl_expiry})")
    return _build_token_response(guest_user)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Identity verification: return authenticated user profile, role, and tenant context."""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Exchange a valid refresh token for a fresh access token."""
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type: expected refresh token"
        )

    user_id = decoded.get("user_id")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return _build_token_response(user)


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user)
):
    """Invalidate active token on backend."""
    revoke_token(token)
    logger.info(f"User '{current_user.username}' logged out and token invalidated")
    return {"message": "Logged out successfully"}
