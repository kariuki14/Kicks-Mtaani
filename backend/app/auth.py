import os
import hmac
import logging
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Security, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db, DATABASE_URL
from app.models import User

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
_DEFAULT_DEV_SECRET = "kicks-mtaani-default-dev-secret-change-in-prod"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_DEV_SECRET)
ALGORITHM = "HS256"

# Fail fast if the default dev secret is used in a production-like environment
if JWT_SECRET_KEY == _DEFAULT_DEV_SECRET:
    if not DATABASE_URL.startswith("sqlite"):
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is not set. "
            "Refusing to start with the default dev secret against a non-SQLite (production) database."
        )
    logger.warning(
        "JWT_SECRET_KEY not set — using insecure default dev secret. "
        "Set it via environment variable before deploying."
    )
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security Schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ─── PASSWORD HASHING (BCRYPT) ───────────────────────────────────
# bcrypt operates on at most 72 bytes; longer inputs are truncated deterministically.
_BCRYPT_MAX_BYTES = 72


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt (truncated to bcrypt's 72-byte limit)."""
    pw_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash (truncated to bcrypt's 72-byte limit)."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


# ─── JWT UTILITIES ───────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── AUTHENTICATION DEPENDENCIES ─────────────────────────────────
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate the currently authenticated user from Bearer token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    email: Optional[str] = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return user


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Validate X-API-Key against server environment configuration."""
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_API_KEY not configured on server"
        )
    if not api_key or not hmac.compare_digest(api_key, ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key


def verify_admin_access(
    api_key: Optional[str] = Security(api_key_header),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    Unified admin verification: accepts EITHER a valid Admin API Key OR an Admin JWT Bearer Token.
    Returns authorization metadata.
    """
    # 1. Try API Key
    if api_key and ADMIN_API_KEY and hmac.compare_digest(api_key, ADMIN_API_KEY):
        return {"auth_type": "api_key", "role": "admin"}

    # 2. Try Bearer JWT
    if token:
        try:
            payload = decode_access_token(token)
            email: Optional[str] = payload.get("sub")
            role: Optional[str] = payload.get("role")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user and user.is_active and (user.role == "admin" or role == "admin"):
                    return {"auth_type": "jwt", "user_id": user.id, "email": user.email, "role": "admin"}
        except HTTPException:
            pass

    # Neither passed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin authorization required (Provide valid X-API-Key or Admin Bearer Token)",
        headers={"WWW-Authenticate": "Bearer"},
    )