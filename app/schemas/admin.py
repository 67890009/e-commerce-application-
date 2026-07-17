from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Seller Management ───────────────────────────────────────────


class SellerListItem(BaseModel):
    """Single seller in the list response."""

    id: UUID
    full_name: str
    email: str
    business_name: str | None
    seller_status: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SellerListResponse(BaseModel):
    """Paginated list of sellers."""

    sellers: list[SellerListItem]
    total: int
    page: int
    limit: int


class SellerDetailResponse(BaseModel):
    """Detailed seller view with counts (counts are 0 until products/orders exist)."""

    id: UUID
    full_name: str
    email: str
    business_name: str | None
    seller_status: str | None
    is_active: bool
    status_reason: str | None
    created_at: datetime
    product_count: int
    order_count: int
    return_count: int

    model_config = ConfigDict(from_attributes=True)


class StatusReasonRequest(BaseModel):
    """Request body for actions that accept an optional reason."""

    reason: str | None = Field(None, max_length=500)


class SellerActionResponse(BaseModel):
    """Returned by approve, reject, suspend, reinstate, ban."""

    message: str
    seller_id: UUID
    seller_status: str


# ── Dashboard ───────────────────────────────────────────────────


class DashboardResponse(BaseModel):
    """Aggregate stats. Values are 0 for modules not yet built."""

    total_users: int
    total_sellers: int
    active_sellers: int
    pending_sellers: int
    restricted_sellers: int