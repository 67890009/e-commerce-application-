from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING.value: {
        OrderStatus.CONFIRMED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.CONFIRMED.value: {
        OrderStatus.SHIPPED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.SHIPPED.value: {
        OrderStatus.DELIVERED.value,
    },
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    shipping_address: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], lazy="joined", innerjoin=True
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], lazy="joined", innerjoin=True
    )
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", lazy="selectin", back_populates="order"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','confirmed','shipped','delivered','cancelled')",
            name="ck_orders_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status}>"


class OrderItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    product_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    product_image: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    order: Mapped["Order"] = relationship(
        "Order", lazy="joined", innerjoin=True
    )

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} product={self.product_name}>"