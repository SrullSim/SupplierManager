import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_token(token: str) -> str:
    """SHA-256 hash used to store refresh tokens without saving the raw value."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload["type"] = "access"
    payload["jti"] = str(uuid.uuid4())
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload["type"] = "refresh"
    payload["jti"] = str(uuid.uuid4())  # ensures uniqueness even when issued in same second
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Raises JWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


__all__ = [
    "hash_password",
    "verify_password",
    "hash_token",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "JWTError",
]
