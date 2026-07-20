from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    seller_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    category_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    compare_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id], lazy="joined", innerjoin=True)  # noqa: F821
    category: Mapped["Category | None"] = relationship("Category", lazy="joined")  # noqa: F821

    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_products_status"),
        CheckConstraint("price >= 0", name="ck_products_price"),
        CheckConstraint("stock >= 0", name="ck_products_stock"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name}>"