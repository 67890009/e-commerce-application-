from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.
    All fields are typed and validated at startup.
    """

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Marketplace"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 420
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google OAuth ─────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # ── Frontend ─────────────────────────────────────────────────
    FRONTEND_URL: str

    # ── Derived ──────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def allowed_origins(self) -> list[str]:
        if self.is_production:
            return [self.FRONTEND_URL]
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            self.FRONTEND_URL,
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton — import this everywhere
settings = Settings()