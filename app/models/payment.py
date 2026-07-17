from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    razorpay_order_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    razorpay_signature: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="INR"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="created"
    )
    platform_commission: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    seller_payout_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    order: Mapped["Order"] = relationship(
        "Order", lazy="joined", innerjoin=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('created','paid','failed','refunded')",
            name="ck_payments_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} status={self.status}>"