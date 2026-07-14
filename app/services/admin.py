from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.admin import (
    PendingSellerResponse,
    PendingSellersListResponse,
    SellerActionResponse,
)


async def list_pending_sellers(
    db: AsyncSession,
) -> PendingSellersListResponse:
    """
    List all sellers waiting for admin approval.

    Pending state: role='seller', seller_approved=FALSE, seller_rejected IS NULL.
    - Customers are excluded by role filter.
    - Approved sellers are excluded by seller_approved=FALSE.
    - Rejected sellers are excluded by seller_rejected IS NULL.
    """
    stmt = (
        select(User)
        .where(
            User.role == "seller",
            User.seller_approved == False,  # noqa: E712
            User.seller_rejected.is_(None),
        )
        .order_by(User.created_at.desc())
    )
    result = await db.execute(stmt)
    sellers = result.scalars().all()

    return PendingSellersListResponse(
        sellers=[PendingSellerResponse.model_validate(s) for s in sellers],
        total=len(sellers),
    )


async def approve_seller(
    db: AsyncSession,
    seller_id: UUID,
) -> SellerActionResponse:
    """
    Approve a pending seller account.
    Raises 404 if the user doesn't exist or isn't a seller.
    Raises 409 if the seller is already approved or already rejected.
    """
    stmt = select(User).where(User.id == seller_id)
    result = await db.execute(stmt)
    seller = result.scalar_one_or_none()

    # Generic 404 — don't reveal whether the ID is wrong or the role is wrong
    if seller is None or seller.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    if seller.seller_approved is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller is already approved.",
        )

    if seller.seller_rejected is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller has already been rejected.",
        )

    seller.seller_approved = True

    return SellerActionResponse(
        message="Seller approved",
        seller_id=seller_id,
    )


async def reject_seller(
    db: AsyncSession,
    seller_id: UUID,
    reason: str | None,
) -> SellerActionResponse:
    """
    Reject a pending seller account.
    Raises 404 if the user doesn't exist or isn't a seller.
    Raises 409 if the seller is already approved or already rejected.
    """
    stmt = select(User).where(User.id == seller_id)
    result = await db.execute(stmt)
    seller = result.scalar_one_or_none()

    if seller is None or seller.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    if seller.seller_approved is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller is already approved.",
        )

    if seller.seller_rejected is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller has already been rejected.",
        )

    seller.seller_rejected = True
    seller.rejection_reason = reason

    return SellerActionResponse(
        message="Seller rejected",
        seller_id=seller_id,
    )