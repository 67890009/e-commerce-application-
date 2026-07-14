from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    GoogleExchangeRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    UserResponse,
)
from app.services import auth as auth_service
from app.services import google_oauth as google_oauth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Rate Limiter ────────────────────────────────────────────────
# Created here, imported by main.py for limiter.init_app(app).
# key_func=get_remote_address uses the client IP.
limiter = Limiter(key_func=get_remote_address)


# ── Register ────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await auth_service.register_user(
        db=db,
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        role=body.role,
    )


# ── Login ───────────────────────────────────────────────────────


@router.post(
    "/login",
    response_model=AuthResponse,
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await auth_service.login_user(
        db=db,
        email=body.email,
        password=body.password,
    )


# ── Google OAuth ────────────────────────────────────────────────


@router.get(
    "/google/login",
    status_code=307,
)
async def google_login() -> RedirectResponse:
    """
    Redirect the browser to Google's consent screen.
    No rate limit — user is leaving our site.
    """
    url = google_oauth_service.get_google_auth_url()
    return RedirectResponse(url=url, status_code=307)


@router.get(
    "/google/callback",
    status_code=307,
)
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Google redirects the browser here after user consents.
    We exchange Google's code for user info, create/link the account,
    generate a one-time code, and redirect to the frontend.
    No rate limit — Google's own flow protects this.
    """
    raw_code = await google_oauth_service.handle_google_callback(
        code=code,
        db=db,
    )
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?code={raw_code}"
    return RedirectResponse(url=redirect_url, status_code=307)


@router.post(
    "/google/exchange",
    response_model=AuthResponse,
)
@limiter.limit("10/minute")
async def google_exchange(
    request: Request,
    body: GoogleExchangeRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await google_oauth_service.exchange_google_code(
        raw_code=body.code,
        db=db,
    )


# ── Refresh Token ───────────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=RefreshResponse,
)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    return await auth_service.refresh_tokens(
        db=db,
        raw_refresh_token=body.refresh_token,
    )


# ── Logout ──────────────────────────────────────────────────────


@router.post(
    "/logout",
    status_code=204,
)
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    await auth_service.logout_user(
        db=db,
        raw_refresh_token=body.refresh_token,
    )
    return Response(status_code=204)


# ── Get Current User ────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)