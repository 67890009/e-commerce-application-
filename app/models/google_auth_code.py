from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GoogleAuthCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "google_auth_codes"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    user: Mapped["User"] = relationship("User", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<GoogleAuthCode id={self.id} user_id={self.user_id} used={self.used}>"