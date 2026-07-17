from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product import ProductPublicListResponse, ProductPublicResponse
from app.services import product as product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=ProductPublicListResponse,
)
async def list_products(
    search: str | None = Query(None),
    category_id: str | None = Query(None),
    sort_by: str | None = Query(None, description="price, name, or created_at"),
    sort_order: str | None = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProductPublicListResponse:
    return await product_service.list_products_public(
        db=db,
        search=search,
        category_id=category_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductPublicResponse,
)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProductPublicResponse:
    return await product_service.get_product_public(
        db=db,
        product_id=product_id,
    )