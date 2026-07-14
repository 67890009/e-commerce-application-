from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GoogleAuthCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Stores short-lived, one-time codes for the Google OAuth redirect flow.
    
    Flow:
    1. Google redirects to backend callback
    2. Backend creates a code, stores the HASH here, redirects browser to frontend with the RAW code
    3. Frontend sends raw code to POST /api/v1/auth/google/exchange
    4. Backend hashes the received code, looks it up here, issues tokens, marks used=TRUE
    """
    __tablename__ = "google_auth_codes"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # ── Relationships ───────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User", lazy="joined", innerjoin=True
    )

    def __repr__(self) -> str:
        return f"<GoogleAuthCode id={self.id} user_id={self.user_id} used={self.used}>"