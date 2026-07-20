from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CartItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cart_items"

    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    cart_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    product: Mapped["Product"] = relationship("Product", lazy="joined", innerjoin=True)  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_cart_product"),
        UniqueConstraint("cart_token", "product_id", name="uq_token_cart_product"),
        CheckConstraint("quantity >= 1", name="ck_cart_items_quantity"),
        CheckConstraint(
            "(user_id IS NOT NULL AND cart_token IS NULL) OR "
            "(user_id IS NULL AND cart_token IS NOT NULL)",
            name="ck_cart_items_owner",
        ),
    )

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} product_id={self.product_id} qty={self.quantity}>"