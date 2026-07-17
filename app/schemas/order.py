from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Nested ──────────────────────────────────────────────────────


class ShippingAddressSchema(BaseModel):
    full_name: str
    phone: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    pincode: str
    country: str


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_price: Decimal
    product_image: str | None
    quantity: int
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


# ── Requests ────────────────────────────────────────────────────


class CreateOrderRequest(BaseModel):
    seller_id: UUID
    shipping_address: ShippingAddressSchema


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(confirmed|shipped|delivered|cancelled)$")


# ── Responses ───────────────────────────────────────────────────


class OrderListItemResponse(BaseModel):
    id: UUID
    seller_id: UUID
    seller_name: str
    seller_business_name: str | None
    total_amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    orders: list[OrderListItemResponse]
    total: int
    page: int
    limit: int


class OrderDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    customer_name: str
    customer_email: str
    seller_id: UUID
    seller_name: str
    seller_business_name: str | None
    total_amount: Decimal
    status: str
    shipping_address: ShippingAddressSchema
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateOrderResponse(BaseModel):
    order: OrderDetailResponse
    razorpay_order_id: str


class OrderStatusUpdateResponse(BaseModel):
    message: str
    order_id: UUID
    status: str