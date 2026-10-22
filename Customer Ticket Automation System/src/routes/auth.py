import logging
from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User
from src.utils.hashing import verify_password
from src.utils.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"Login failed: user '{username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not verify_password(password, user.password_hash):
        logger.warning(f"Login failed: invalid password for user '{username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "email": user.email
        }
    )

    logger.info(f"User '{username}' authenticated successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username
    }
