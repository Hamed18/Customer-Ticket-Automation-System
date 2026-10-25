import logging
from datetime import datetime, timezone
from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.Users import User
from src.utils.jwt_handler import decode_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

AGENT_ROLES = {
    "Lead Support Agent",
    "Support Specialist",
    "Tier 2 Support",
    "Admin",
    "agent",
    "admin"
}

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer token, check revocation/TTL, and load user record."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)

    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cannot be used as an access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    username = payload.get("sub")

    if not user_id and not username:
        raise credentials_exception

    user = None
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
    if not user and username:
        user = db.query(User).filter(User.username == username).first()

    if not user:
        raise credentials_exception

    # Check guest session TTL expiry
    if user.is_guest and user.expires_at:
        now = datetime.now(timezone.utc)
        expires_at = user.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest session has expired. Please start a new session.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user

def get_current_active_agent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure authenticated caller has an agent or administrative role."""
    if current_user.role not in AGENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Agent or Admin role required"
        )
    return current_user

def require_roles(*allowed_roles: str) -> Callable:
    """Role-Based Access Control (RBAC) dependency factory."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles}"
            )
        return current_user
    return role_checker
