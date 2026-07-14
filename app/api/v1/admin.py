from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.admin import (
    PendingSellersListResponse,
    RejectSellerRequest,
    SellerActionResponse,
)
from app.services import admin as admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/sellers/pending",
    response_model=PendingSellersListResponse,
)
async def list_pending_sellers(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> PendingSellersListResponse:
    """
    List all sellers waiting for approval.
    Requires admin role.
    """
    return await admin_service.list_pending_sellers(db=db)


@router.post(
    "/sellers/{seller_id}/approve",
    response_model=SellerActionResponse,
)
async def approve_seller(
    seller_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """
    Approve a pending seller account.
    Requires admin role.
    """
    return await admin_service.approve_seller(
        db=db,
        seller_id=seller_id,
    )


@router.post(
    "/sellers/{seller_id}/reject",
    response_model=SellerActionResponse,
)
async def reject_seller(
    seller_id: str,
    body: RejectSellerRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """
    Reject a pending seller account.
    Optionally include a reason.
    Requires admin role.
    """
    return await admin_service.reject_seller(
        db=db,
        seller_id=seller_id,
        reason=body.reason if body else None,
    )