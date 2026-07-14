from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, RefreshResponse, UserResponse


# ── Internal Helpers ────────────────────────────────────────────


async def _create_token_pair(
    user: User,
) -> tuple[str, str, str, datetime]:
    """
    Generate a new access token + refresh token pair.
    Returns (access_token, raw_refresh, hashed_refresh, expires_at).
    """
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        seller_approved=user.seller_approved,
    )

    raw_refresh = generate_refresh_token()
    hashed_refresh = hash_refresh_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    return access_token, raw_refresh, hashed_refresh, expires_at


async def _store_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    hashed_token: str,
    expires_at: datetime,
) -> None:
    """Insert a new refresh token row into the database."""
    token = RefreshToken(
        token_hash=hashed_token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(token)


def _build_auth_response(
    user: User,
    access_token: str,
    raw_refresh_token: str,
) -> AuthResponse:
    """Build the standard AuthResponse returned by register, login, and Google exchange."""
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=raw_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


# ── Public Services ─────────────────────────────────────────────


async def register_user(
    db: AsyncSession,
    full_name: str,
    email: str,
    password: str,
    role: str,
) -> AuthResponse:
    """
    Register a new customer or seller account.
    Raises 409 if email is already registered.
    """
    # Check email uniqueness
    stmt = select(User).where(User.email == email.lower())
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    # Create user
    user = User(
        full_name=full_name,
        email=email.lower(),
        hashed_password=hash_password(password),
        role=role,
        seller_approved=False if role == "seller" else None,
        seller_rejected=None,
    )
    db.add(user)
    await db.flush()  # Assigns user.id without committing

    # Create token pair
    access_token, raw_refresh, hashed_refresh, expires_at = (
        await _create_token_pair(user)
    )
    await _store_refresh_token(db, user.id, hashed_refresh, expires_at)

    return _build_auth_response(user, access_token, raw_refresh)


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> AuthResponse:
    """
    Authenticate with email + password.
    Raises 401 with a generic message — never reveals whether email or password is wrong.
    """
    stmt = select(User).where(User.email == email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Generic failure — same message whether user not found, password wrong,
    # or account has no password (Google-only account).
    if user is None or not verify_password(password, user.hashed_password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled.",
        )

    # Create token pair
    access_token, raw_refresh, hashed_refresh, expires_at = (
        await _create_token_pair(user)
    )
    await _store_refresh_token(db, user.id, hashed_refresh, expires_at)

    return _build_auth_response(user, access_token, raw_refresh)


async def refresh_tokens(
    db: AsyncSession,
    raw_refresh_token: str,
) -> RefreshResponse:
    """
    Rotate a refresh token.
    - Old token is marked revoked.
    - New token pair is issued.
    - If a revoked token is reused, ALL tokens for that user are revoked (theft detection).
    Raises 401 on any failure.
    """
    token_hash = hash_refresh_token(raw_refresh_token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    # Token not found in database
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # Token has expired
    if now > token_record.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired.",
        )

    # ── ROTATION VIOLATION — POSSIBLE THEFT ────────────────────
    # This token was already used once (revoked=True) and someone
    # is presenting it again. Revoke ALL tokens for this user
    # to force a full re-login from both the legitimate user and the attacker.
    if token_record.revoked:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == token_record.user_id)
            .values(revoked=True)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. Please log in again.",
        )

    # Token is valid — perform rotation
    token_record.revoked = True

    # user is loaded via lazy="joined" — no extra query
    user = token_record.user

    access_token, raw_new_refresh, hashed_new_refresh, new_expires_at = (
        await _create_token_pair(user)
    )
    await _store_refresh_token(db, user.id, hashed_new_refresh, new_expires_at)

    return RefreshResponse(
        access_token=access_token,
        refresh_token=raw_new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


async def logout_user(
    db: AsyncSession,
    raw_refresh_token: str,
) -> None:
    """
    Revoke a specific refresh token.
    Silently succeeds if token is not found (may have already expired/been cleaned up).
    """
    token_hash = hash_refresh_token(raw_refresh_token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if token_record is not None:
        token_record.revoked = True