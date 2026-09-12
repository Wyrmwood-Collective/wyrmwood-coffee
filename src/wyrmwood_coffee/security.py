"""Password hashing and JWT helpers."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from wyrmwood_coffee.settings import app_settings


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=app_settings().auth.jwt_expiration_minutes)
    )
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(
        to_encode,
        app_settings().auth.jwt_secret_key,
        algorithm=app_settings().auth.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    return jwt.decode(
        token,
        app_settings().auth.jwt_secret_key,
        algorithms=[app_settings().auth.jwt_algorithm],
    )
