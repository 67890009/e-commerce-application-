from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    """Allowed user roles. Inherits from str so JSON serialization works naturally."""

    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    seller_rejected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('customer', 'seller', 'admin')",
            name="ck_users_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"