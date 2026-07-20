import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ────────────────────────────────────────────────────────────────
# Password Hashing
# ────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        salt,
    )
    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


# ────────────────────────────────────────────────────────────────
# JWT Access Tokens
# ────────────────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    role: str,
    seller_approved: bool | None,
) -> str:
    """
    Create a signed JWT access token.
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "role": role,
        "seller_approved": seller_approved,
        "iat": now,
        "exp": now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS),
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify an access token.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


# ────────────────────────────────────────────────────────────────
# Refresh Tokens
# ────────────────────────────────────────────────────────────────


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token before storing it."""
    return hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()


def refresh_token_expiry() -> datetime:
    """Return refresh token expiry timestamp."""
    return datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )


# ────────────────────────────────────────────────────────────────
# Google OAuth
# ────────────────────────────────────────────────────────────────


def generate_oauth_code() -> str:
    """Generate a one-time OAuth exchange code."""
    return secrets.token_urlsafe(32)


def hash_oauth_code(code: str) -> str:
    """Hash the OAuth code before storing it."""
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()