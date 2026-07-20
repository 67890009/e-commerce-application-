from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SellerStatus, User
from app.schemas.admin import (
    SellerActionResponse,
    SellerDetailResponse,
    SellerListResponse,
    SellerListItem,
    DashboardResponse,
)


# ── Seller Management ───────────────────────────────────────────


async def list_sellers(
    db: AsyncSession,
    status: str | None,
    search: str | None,
    page: int,
    limit: int,
) -> SellerListResponse:
    """
    List all sellers with optional filtering and search.
    """
    query = select(User).where(User.role == "seller")

    if status is not None:
        query = query.where(User.seller_status == status)

    if search is not None:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term),
                User.business_name.ilike(search_term),
            )
        )

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    sellers = result.scalars().all()

    return SellerListResponse(
        sellers=[SellerListItem.model_validate(s) for s in sellers],
        total=total,
        page=page,
        limit=limit,
    )


async def get_seller_detail(
    db: AsyncSession,
    seller_id: str,
) -> SellerDetailResponse:
    """
    Get detailed info for a single seller.
    Product/order/return counts are 0 until those tables exist.
    """
    import uuid
    uid = uuid.UUID(str(seller_id))
    stmt = select(User).where(
        User.id == uid,
        User.role == "seller",
    )
    result = await db.execute(stmt)
    seller = result.scalar_one_or_none()

    if seller is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    return SellerDetailResponse(
        id=seller.id,
        full_name=seller.full_name,
        email=seller.email,
        business_name=seller.business_name,
        seller_status=seller.seller_status,
        is_active=seller.is_active,
        status_reason=seller.status_reason,
        created_at=seller.created_at,
        product_count=0,
        order_count=0,
        return_count=0,
    )


async def approve_seller(
    db: AsyncSession,
    seller_id: str,
) -> SellerActionResponse:
    """
    Approve a pending seller.
    """
    seller = await _get_seller_by_id(db, seller_id)

    if seller.seller_status == SellerStatus.APPROVED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller is already approved.",
        )

    if seller.seller_status == SellerStatus.BANNED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot approve a banned seller.",
        )

    seller.seller_status = SellerStatus.APPROVED.value
    seller.status_reason = None

    return SellerActionResponse(
        message="Seller approved",
        seller_id=seller.id,
        seller_status=SellerStatus.APPROVED.value,
    )


async def reject_seller(
    db: AsyncSession,
    seller_id: str,
    reason: str | None,
) -> SellerActionResponse:
    """
    Reject a pending seller.
    """
    seller = await _get_seller_by_id(db, seller_id)

    if seller.seller_status == SellerStatus.REJECTED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller is already rejected.",
        )

    if seller.seller_status == SellerStatus.BANNED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot reject a banned seller.",
        )

    seller.seller_status = SellerStatus.REJECTED.value
    seller.status_reason = reason

    return SellerActionResponse(
        message="Seller rejected",
        seller_id=seller.id,
        seller_status=SellerStatus.REJECTED.value,
    )


async def suspend_seller(
    db: AsyncSession,
    seller_id: str,
    reason: str | None,
) -> SellerActionResponse:
    """
    Suspend an approved seller (reversible).
    """
    seller = await _get_seller_by_id(db, seller_id)

    if seller.seller_status != SellerStatus.APPROVED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only approved sellers can be suspended.",
        )

    seller.seller_status = SellerStatus.SUSPENDED.value
    seller.status_reason = reason

    return SellerActionResponse(
        message="Seller suspended",
        seller_id=seller.id,
        seller_status=SellerStatus.SUSPENDED.value,
    )


async def reinstate_seller(
    db: AsyncSession,
    seller_id: str,
) -> SellerActionResponse:
    """
    Reinstate a suspended seller back to approved.
    """
    seller = await _get_seller_by_id(db, seller_id)

    if seller.seller_status != SellerStatus.SUSPENDED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only suspended sellers can be reinstated.",
        )

    seller.seller_status = SellerStatus.APPROVED.value
    seller.status_reason = None

    return SellerActionResponse(
        message="Seller reinstated",
        seller_id=seller.id,
        seller_status=SellerStatus.APPROVED.value,
    )


async def ban_seller(
    db: AsyncSession,
    seller_id: str,
    reason: str | None,
) -> SellerActionResponse:
    """
    Permanently ban a seller. Not reversible. Blocks login.
    """
    seller = await _get_seller_by_id(db, seller_id)

    if seller.seller_status == SellerStatus.BANNED.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller is already banned.",
        )

    seller.seller_status = SellerStatus.BANNED.value
    seller.status_reason = reason

    return SellerActionResponse(
        message="Seller banned",
        seller_id=seller.id,
        seller_status=SellerStatus.BANNED.value,
    )


# ── Dashboard ───────────────────────────────────────────────────


async def get_dashboard_stats(
    db: AsyncSession,
) -> DashboardResponse:
    """
    Aggregate stats from users table only.
    Product/order/revenue counts are 0 until those modules exist.
    """
    total_users = await db.scalar(
        select(func.count()).where(User.role == "customer")
    ) or 0

    total_sellers = await db.scalar(
        select(func.count()).where(User.role == "seller")
    ) or 0

    active_sellers = await db.scalar(
        select(func.count()).where(
            User.role == "seller",
            User.seller_status == SellerStatus.APPROVED.value,
        )
    ) or 0

    pending_sellers = await db.scalar(
        select(func.count()).where(
            User.role == "seller",
            User.seller_status == SellerStatus.PENDING.value,
        )
    ) or 0

    restricted_sellers = await db.scalar(
        select(func.count()).where(
            User.role == "seller",
            User.seller_status.in_([
                SellerStatus.SUSPENDED.value,
                SellerStatus.BANNED.value,
            ]),
        )
    ) or 0

    return DashboardResponse(
        total_users=total_users,
        total_sellers=total_sellers,
        active_sellers=active_sellers,
        pending_sellers=pending_sellers,
        restricted_sellers=restricted_sellers,
    )


# ── Internal Helpers ────────────────────────────────────────────


async def _get_seller_by_id(
    db: AsyncSession,
    seller_id: str,
) -> User:
    """Fetch a seller by ID. Raises 404 if not found or not a seller."""
    from fastapi import HTTPException, status
    import uuid
    uid = uuid.UUID(str(seller_id))

    stmt = select(User).where(User.id == uid, User.role == "seller")
    result = await db.execute(stmt)
    seller = result.scalar_one_or_none()

    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    return seller