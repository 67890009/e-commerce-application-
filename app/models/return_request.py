from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ReturnReason(str, enum.Enum):
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    OTHER = "other"


class ReturnStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUND_INITIATED = "refund_initiated"
    REFUND_COMPLETED = "refund_completed"


_REASON_VALUES = "'defective','wrong_item','not_as_described','changed_mind','other'"
_STATUS_VALUES = "'pending','approved','rejected','refund_initiated','refund_completed'"


class ReturnRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "return_requests"

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    razorpay_refund_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    order: Mapped["Order"] = relationship("Order", lazy="joined", back_populates="return_request")  # noqa: F821
    user: Mapped["User"] = relationship("User", lazy="joined")  # noqa: F821

    __table_args__ = (
        CheckConstraint(f"reason IN ({_REASON_VALUES})", name="ck_return_requests_reason"),
        CheckConstraint(f"status IN ({_STATUS_VALUES})", name="ck_return_requests_status"),
    )