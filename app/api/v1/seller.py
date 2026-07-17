from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_seller
from app.models.user import User
from app.schemas.product import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services import product as product_service
from app.schemas.order import OrderDetailResponse, OrderListResponse
from app.services import order as order_service

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
)
async def create_product(
    body: ProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(require_seller),
) -> ProductResponse:
    return await product_service.create_product(
        db=db,
        seller_id=str(seller.id),
        data=body,
    )


@router.get(
    "/products",
    response_model=ProductListResponse,
)
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(require_seller),
) -> ProductListResponse:
    return await product_service.list_seller_products(
        db=db,
        seller_id=str(seller.id),
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
    seller: User = Depends(require_seller),
) -> ProductResponse:
    return await product_service.get_seller_product(
        db=db,
        seller_id=str(seller.id),
        product_id=product_id,
    )


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: str,
    body: ProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(require_seller),
) -> ProductResponse:
    return await product_service.update_seller_product(
        db=db,
        seller_id=str(seller.id),
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
    seller: User = Depends(require_seller),
) -> None:
    await product_service.delete_seller_product(
        db=db,
        seller_id=str(seller.id),
        product_id=product_id,
    )

# ── Orders ──────────────────────────────────────────────────────


@router.get(
    "/orders",
    response_model=OrderListResponse,
)
async def list_seller_orders(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(require_seller),
) -> OrderListResponse:
    return await order_service.list_seller_orders(
        db=db,
        seller_id=str(seller.id),
        status_filter=status,
        page=page,
        limit=limit,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
)
async def get_seller_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(require_seller),
) -> OrderDetailResponse:
    return await order_service.get_seller_order(
        db=db,
        seller_id=str(seller.id),
        order_id=order_id,
    )