from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddToCartRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(1, ge=1)


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_price: Decimal
    product_image: str | None
    product_stock: int
    seller_id: UUID
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    total_amount: Decimal


class MergeCartRequest(BaseModel):
    cart_token: str


class MergeCartResponse(BaseModel):
    message: str
    items_count: int