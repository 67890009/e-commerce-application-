from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Requests ────────────────────────────────────────────────────


class RejectSellerRequest(BaseModel):
    reason: str | None = Field(
        None,
        max_length=1000,
        description="Optional reason for rejection. Shown to the seller.",
    )


# ── Responses ───────────────────────────────────────────────────


class PendingSellerResponse(BaseModel):
    """Single seller in the pending sellers list."""

    id: UUID
    full_name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PendingSellersListResponse(BaseModel):
    """Wrapper for the list of pending sellers with total count."""

    sellers: list[PendingSellerResponse]
    total: int


class SellerActionResponse(BaseModel):
    """Returned by both approve and reject endpoints."""

    message: str
    seller_id: UUID