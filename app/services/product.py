from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductStatus
from app.schemas.product import (
    ProductAdminEditRequest,
    ProductCreateRequest,
    ProductListResponse,
    ProductListItemResponse,
    ProductPublicListResponse,
    ProductPublicResponse,
    ProductResponse,
    ProductUpdateRequest,
)


async def create_product(
    db: AsyncSession,
    seller_id: str,
    data: ProductCreateRequest,
) -> ProductResponse:
    product = Product(
        seller_id=seller_id,
        category_id=str(data.category_id),
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
        image_url=data.image_url,
        status=ProductStatus.ACTIVE.value,
    )
    db.add(product)
    await db.flush()
    return ProductResponse.model_validate(product)


async def list_seller_products(
    db: AsyncSession,
    seller_id: str,
    page: int,
    limit: int,
) -> ProductListResponse:
    query = select(Product).where(
        Product.seller_id == seller_id,
        Product.is_active == True,  # noqa: E712
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        products=[ProductListItemResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
    )


async def get_seller_product(
    db: AsyncSession,
    seller_id: str,
    product_id: str,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)

    if product.seller_id != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this product.",
        )

    return ProductResponse.model_validate(product)


async def update_seller_product(
    db: AsyncSession,
    seller_id: str,
    product_id: str,
    data: ProductUpdateRequest,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)

    if product.seller_id != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this product.",
        )

    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.price is not None:
        product.price = data.price
    if data.stock is not None:
        product.stock = data.stock
    if data.category_id is not None:
        product.category_id = str(data.category_id)
    if data.image_url is not None:
        product.image_url = data.image_url

    await db.flush()
    return ProductResponse.model_validate(product)


async def delete_seller_product(
    db: AsyncSession,
    seller_id: str,
    product_id: str,
) -> None:
    product = await _get_product_by_id(db, product_id)

    if product.seller_id != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this product.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already deleted.",
        )

    product.is_active = False


# ── Admin ───────────────────────────────────────────────────────


async def list_products_admin(
    db: AsyncSession,
    search: str | None,
    status_filter: str | None,
    category_id: str | None,
    page: int,
    limit: int,
) -> ProductListResponse:
    query = select(Product).where(Product.is_active == True)  # noqa: E712

    if search is not None:
        term = f"%{search}%"
        query = query.where(Product.name.ilike(term))

    if status_filter is not None:
        query = query.where(Product.status == status_filter)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        products=[ProductListItemResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
    )


async def get_product_admin(
    db: AsyncSession,
    product_id: str,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)
    return ProductResponse.model_validate(product)


async def disable_product_admin(
    db: AsyncSession,
    product_id: str,
    reason: str | None,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)

    if product.status == ProductStatus.DISABLED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already disabled.",
        )

    product.status = ProductStatus.DISABLED.value
    product.disabled_reason = reason
    await db.flush()
    return ProductResponse.model_validate(product)


async def enable_product_admin(
    db: AsyncSession,
    product_id: str,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)

    if product.status == ProductStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already active.",
        )

    product.status = ProductStatus.ACTIVE.value
    product.disabled_reason = None
    await db.flush()
    return ProductResponse.model_validate(product)


async def edit_product_admin(
    db: AsyncSession,
    product_id: str,
    data: ProductAdminEditRequest,
) -> ProductResponse:
    product = await _get_product_by_id(db, product_id)

    product.name = data.name
    product.description = data.description
    product.price = data.price
    product.stock = data.stock
    product.category_id = str(data.category_id)
    product.image_url = data.image_url
    await db.flush()
    return ProductResponse.model_validate(product)


async def delete_product_admin(
    db: AsyncSession,
    product_id: str,
) -> None:
    product = await _get_product_by_id(db, product_id)

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already deleted.",
        )

    product.is_active = False


# ── Public ──────────────────────────────────────────────────────


async def list_products_public(
    db: AsyncSession,
    search: str | None,
    category_id: str | None,
    sort_by: str | None,
    sort_order: str | None,
    page: int,
    limit: int,
) -> ProductPublicListResponse:
    query = select(Product).where(
        Product.is_active == True,  # noqa: E712
        Product.status == ProductStatus.ACTIVE.value,
    )

    if search is not None:
        term = f"%{search}%"
        query = query.where(Product.name.ilike(term))

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    sort_column = Product.created_at
    if sort_by == "price":
        sort_column = Product.price
    elif sort_by == "name":
        sort_column = Product.name

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductPublicListResponse(
        products=[ProductPublicResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
    )


async def get_product_public(
    db: AsyncSession,
    product_id: str,
) -> ProductPublicResponse:
    stmt = select(Product).where(
        Product.id == product_id,
        Product.is_active == True,  # noqa: E712
        Product.status == ProductStatus.ACTIVE.value,
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return ProductPublicResponse.model_validate(product)


# ── Internal ────────────────────────────────────────────────────


async def _get_product_by_id(
    db: AsyncSession,
    product_id: str,
) -> Product:
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product