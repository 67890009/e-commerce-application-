from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Requests ────────────────────────────────────────────────────


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(..., ge=0)
    category_id: UUID
    image_url: str | None = Field(None, max_length=500)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(None, gt=0, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    category_id: UUID | None = None
    image_url: str | None = Field(None, max_length=500)


class ProductAdminEditRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(..., ge=0)
    category_id: UUID
    image_url: str | None = Field(None, max_length=500)


class ReasonRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


# ── Responses ───────────────────────────────────────────────────


class ProductResponse(BaseModel):
    id: UUID
    seller_id: UUID
    category_id: UUID | None = None
    name: str
    description: str | None
    price: Decimal
    compare_price: Decimal | None = None
    stock: int
    image_url: str | None
    status: str
    disabled_reason: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListItemResponse(BaseModel):
    id: UUID
    name: str
    price: Decimal
    compare_price: Decimal | None = None
    stock: int
    image_url: str | None
    category_id: UUID | None = None
    seller_id: UUID
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductPublicResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    price: Decimal
    compare_price: Decimal | None = None
    stock: int
    image_url: str | None
    category_id: UUID | None = None
    seller_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    products: list[ProductListItemResponse]
    total: int
    page: int
    limit: int


class ProductPublicListResponse(BaseModel):
    products: list[ProductPublicResponse]
    total: int
    page: int
    limit: int