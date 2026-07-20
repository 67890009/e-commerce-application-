from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_oauth_code,
    generate_refresh_token,
    hash_oauth_code,
    hash_refresh_token,
)
from app.models.google_auth_code import GoogleAuthCode
from app.models.refresh_token import RefreshToken
from app.models.user import SellerStatus, User
from app.schemas.auth import AuthResponse, UserResponse

# ── Google OAuth Endpoints ──────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

_OAUTH_CODE_TTL_SECONDS = 60


# ── Public Services ─────────────────────────────────────────────


def get_google_auth_url() -> str:
    """
    Build the Google OAuth consent screen URL.
    Called by the GET /auth/google/login endpoint.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def handle_google_callback(
    code: str,
    db: AsyncSession,
) -> str:
    """
    Handle the redirect back from Google after user consents.

    Steps:
    1. Exchange the authorization code for a Google access token.
    2. Use that token to fetch the user's profile from Google.
    3. Create a new user or link Google identity to an existing account.
    4. Generate a short-lived one-time code, store its hash.
    5. Return the RAW one-time code.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Exchange code for Google access token
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code != 200:
            try:
                err_data = token_resp.json()
                msg = err_data.get("error_description") or err_data.get("error") or token_resp.text
            except Exception:
                msg = token_resp.text
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code with Google: {msg}",
            )

        token_data = token_resp.json()
        google_access_token = token_data.get("access_token")

        if not google_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token in Google response.",
            )

        # Step 2: Fetch user info
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user info from Google.",
            )

        userinfo = userinfo_resp.json()

    google_id = userinfo.get("id")
    email = userinfo.get("email", "").lower()
    full_name = userinfo.get("name", "")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user info received from Google.",
        )

    # Step 3: Create or link user
    user = await _get_or_create_user(db, google_id, email, full_name)

    # Step 4: Generate one-time code
    raw_code = generate_oauth_code()
    hashed_code = hash_oauth_code(raw_code)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=_OAUTH_CODE_TTL_SECONDS,
    )

    auth_code = GoogleAuthCode(
        code_hash=hashed_code,
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(auth_code)

    # Step 5: Return raw code for the frontend redirect
    return raw_code


async def exchange_google_code(
    raw_code: str,
    db: AsyncSession,
) -> AuthResponse:
    """
    Exchange a one-time code (from the frontend URL) for JWT tokens.
    Called by POST /auth/google/exchange.
    """
    code_hash = hash_oauth_code(raw_code)

    stmt = select(GoogleAuthCode).where(GoogleAuthCode.code_hash == code_hash)
    result = await db.execute(stmt)
    auth_code_record = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if auth_code_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code.",
        )

    if now > auth_code_record.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired.",
        )

    if auth_code_record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code already used.",
        )

    # Mark as used — prevents replay attacks
    auth_code_record.used = True

    # User is loaded via lazy="joined" relationship
    user = auth_code_record.user

    # Issue token pair
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        seller_approved=user.seller_status == SellerStatus.APPROVED.value,
    )

    raw_refresh = generate_refresh_token()
    hashed_refresh = hash_refresh_token(raw_refresh)
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    refresh_token = RefreshToken(
        token_hash=hashed_refresh,
        user_id=user.id,
        expires_at=refresh_expires_at,
    )
    db.add(refresh_token)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


# ── Internal Helpers ────────────────────────────────────────────


async def _get_or_create_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    full_name: str,
) -> User:
    """
    Find existing user by email and link the Google identity,
    or create a brand new customer account.

    Auto-linking behavior (per contract):
    - If the email already exists from a password signup,
      attach the google_id to that account.
    - The user can then log in via either method.
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        # Auto-link: attach Google identity if not already linked
        if user.google_id is None:
            user.google_id = google_id
        return user

    # New user — Google signups are always customers.
    user = User(
        full_name=full_name or email.split("@")[0],
        email=email,
        hashed_password=None,
        google_id=google_id,
        role="customer",
        seller_status=None,
    )
    db.add(user)
    await db.flush()

    return user