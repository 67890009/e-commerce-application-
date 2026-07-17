from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.admin import (
    DashboardResponse,
    SellerActionResponse,
    SellerDetailResponse,
    SellerListResponse,
    StatusReasonRequest,
)
from app.services import admin as admin_service
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.services import category as category_service
from app.schemas.product import (
    ProductAdminEditRequest,
    ProductListResponse,
    ProductResponse,
    ReasonRequest,
)
from app.services import product as product_service
from app.schemas.order import (
    OrderDetailResponse,
    OrderListResponse,
    OrderStatusUpdateResponse,
    UpdateOrderStatusRequest,
)
from app.services import order as order_service


router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Seller Management ───────────────────────────────────────────


@router.get(
    "/sellers",
    response_model=SellerListResponse,
)
async def list_sellers(
    status: str | None = Query(None, description="Filter by seller status"),
    search: str | None = Query(None, description="Search by email, name, or business name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerListResponse:
    """List all sellers with optional filtering and search."""
    return await admin_service.list_sellers(
        db=db,
        status=status,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/sellers/{seller_id}",
    response_model=SellerDetailResponse,
)
async def get_seller_detail(
    seller_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerDetailResponse:
    """Get detailed info for a single seller."""
    return await admin_service.get_seller_detail(
        db=db,
        seller_id=seller_id,
    )


@router.post(
    "/sellers/{seller_id}/approve",
    response_model=SellerActionResponse,
)
async def approve_seller(
    seller_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """Approve a pending seller."""
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
    body: StatusReasonRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """Reject a pending seller."""
    return await admin_service.reject_seller(
        db=db,
        seller_id=seller_id,
        reason=body.reason if body else None,
    )


@router.post(
    "/sellers/{seller_id}/suspend",
    response_model=SellerActionResponse,
)
async def suspend_seller(
    seller_id: str,
    body: StatusReasonRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """Suspend an approved seller (reversible)."""
    return await admin_service.suspend_seller(
        db=db,
        seller_id=seller_id,
        reason=body.reason if body else None,
    )


@router.post(
    "/sellers/{seller_id}/reinstate",
    response_model=SellerActionResponse,
)
async def reinstate_seller(
    seller_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """Reinstate a suspended seller back to approved."""
    return await admin_service.reinstate_seller(
        db=db,
        seller_id=seller_id,
    )


@router.post(
    "/sellers/{seller_id}/ban",
    response_model=SellerActionResponse,
)
async def ban_seller(
    seller_id: str,
    body: StatusReasonRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SellerActionResponse:
    """Permanently ban a seller. Not reversible. Blocks login."""
    return await admin_service.ban_seller(
        db=db,
        seller_id=seller_id,
        reason=body.reason if body else None,
    )
# ── Category Management ─────────────────────────────────────────


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=201,
)
async def create_category(
    body: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> CategoryResponse:
    """Create a new category."""
    return await category_service.create_category(db=db, data=body)


@router.get(
    "/categories",
    response_model=CategoryListResponse,
)
async def list_categories(
    search: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> CategoryListResponse:
    """List all categories including inactive. Supports search and filter."""
    return await category_service.list_categories_admin(
        db=db,
        search=search,
        status_filter=status,
        page=page,
        limit=limit,
    )


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
)
async def update_category(
    category_id: str,
    body: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> CategoryResponse:
    """Update a category."""
    return await category_service.update_category(
        db=db,
        category_id=category_id,
        data=body,
    )


@router.delete(
    "/categories/{category_id}",
    status_code=204,
)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> None:
    """Soft delete a category (sets is_active to false)."""
    await category_service.delete_category(
        db=db,
        category_id=category_id,
    )

# ── Dashboard ───────────────────────────────────────────────────


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DashboardResponse:
    """Get aggregate dashboard stats."""
    return await admin_service.get_dashboard_stats(db=db)
# ── Product Management ──────────────────────────────────────────


@router.get(
    "/products",
    response_model=ProductListResponse,
)
async def list_products(
    search: str | None = Query(None),
    status: str | None = Query(None),
    category_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ProductListResponse:
    return await product_service.list_products_admin(
        db=db,
        search=search,
        status_filter=status,
        category_id=category_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ProductResponse:
    return await product_service.get_product_admin(
        db=db,
        product_id=product_id,
    )


@router.post(
    "/products/{product_id}/disable",
    response_model=ProductResponse,
)
async def disable_product(
    product_id: str,
    body: ReasonRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ProductResponse:
    return await product_service.disable_product_admin(
        db=db,
        product_id=product_id,
        reason=body.reason if body else None,
    )


@router.post(
    "/products/{product_id}/enable",
    response_model=ProductResponse,
)
async def enable_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ProductResponse:
    return await product_service.enable_product_admin(
        db=db,
        product_id=product_id,
    )


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
)
async def edit_product(
    product_id: str,
    body: ProductAdminEditRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ProductResponse:
    return await product_service.edit_product_admin(
        db=db,
        product_id=product_id,
        data=body,
    )


@router.delete(
    "/products/{product_id}",
    status_code=204,
)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> None:
    await product_service.delete_product_admin(
        db=db,
        product_id=product_id,
    )
# ── Order Management ────────────────────────────────────────────


@router.get(
    "/orders",
    response_model=OrderListResponse,
)
async def list_orders(
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> OrderListResponse:
    return await order_service.list_orders_admin(
        db=db,
        status_filter=status,
        user_id=user_id,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> OrderDetailResponse:
    return await order_service.get_order_admin(
        db=db,
        order_id=order_id,
    )


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderStatusUpdateResponse,
)
async def update_order_status(
    order_id: str,
    body: UpdateOrderStatusRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> OrderStatusUpdateResponse:
    return await order_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=body.status,
    )