from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # ── Relationships ───────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User", lazy="joined", innerjoin=True
    )

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.revoked}>"