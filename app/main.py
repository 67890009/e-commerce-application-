from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import limiter
from app.api.v1.router import v1_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — runs once at startup and once at shutdown.
    Replace the yield with startup/shutdown logic as needed
    (e.g., create initial admin user, warm caches).
    """
    yield


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiter ─────────────────────────────────────────────────

app.state.limiter = limiter

# ── Routes ───────────────────────────────────────────────────────

app.include_router(v1_router)


# ── Global Exception Handler ─────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.
    In production, this prevents stack traces from leaking to clients.
    In development, we let the exception through for debugging.
    """
    if settings.DEBUG:
        raise exc

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )