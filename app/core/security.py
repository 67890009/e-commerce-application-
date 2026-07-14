import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

# ── Password Hashing ────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    import bcrypt

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    import bcrypt

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── JWT Access Tokens ───────────────────────────────────────────


def create_access_token(
    user_id: str,
    role: str,
    seller_approved: bool | None,
) -> str:
    """
    Create a signed JWT access token.
    Payload contains only what the frontend needs for authorization decisions.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "seller_approved": seller_approved,
        "iat": now,
        "exp": now + timedelta(seconds=__access_token_delta()),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify an access token.
    Returns the payload dict on success, None on any failure.
    None is always returned — callers never know WHY it failed.
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


# ── Refresh Tokens ──────────────────────────────────────────────
# Raw token is returned to the client.
# SHA-256 hash is stored in the database.
# We never store the raw token — if the DB is compromised, tokens are safe.


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token (raw string)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hash of the raw refresh token — this is what goes in the DB."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ── Google OAuth One-Time Code ──────────────────────────────────


def generate_oauth_code() -> str:
    """Generate a short-lived one-time code for the Google OAuth redirect flow."""
    return secrets.token_urlsafe(32)


def hash_oauth_code(code: str) -> str:
    """SHA-256 hash of the OAuth code for database storage."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# ── Internal Helpers ────────────────────────────────────────────


def __access_token_delta() -> int:
    """Return access token TTL in seconds from settings."""
    return settings.ACCESS_TOKEN_EXPIRE_SECONDS