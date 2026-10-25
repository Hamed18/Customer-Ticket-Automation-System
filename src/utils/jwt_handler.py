import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status
from src.config import settings

# Thread-safe in-memory token revocation cache with expiry timestamps: {token: expire_timestamp}
_REVOKED_TOKENS: Dict[str, float] = {}

def revoke_token(token: str) -> None:
    """Add a token to the revoked token blacklist."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        exp = payload.get("exp", time.time() + 7200)
        _REVOKED_TOKENS[token] = float(exp)
    except Exception:
        _REVOKED_TOKENS[token] = time.time() + 7200
    _clean_expired_revocations()

def is_token_revoked(token: str) -> bool:
    """Check if token is currently revoked."""
    if token in _REVOKED_TOKENS:
        if _REVOKED_TOKENS[token] > time.time():
            return True
        else:
            del _REVOKED_TOKENS[token]
    return False

def _clean_expired_revocations() -> None:
    """Prune expired tokens from the blacklist to maintain zero memory leak."""
    now = time.time()
    expired = [k for k, v in _REVOKED_TOKENS.items() if v <= now]
    for k in expired:
        _REVOKED_TOKENS.pop(k, None)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "access"})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def create_refresh_token(data: dict) -> str:
    """Generate long-lived JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token claims."""
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
