from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)


async def create_category(
    db: AsyncSession,
    data: CategoryCreateRequest,
) -> CategoryResponse:
    existing = await db.scalar(
        select(Category).where(
            or_(
                Category.name == data.name,
                Category.slug == data.slug,
            )
        )
    )
    if existing is not None:
        field = "name" if existing.name == data.name else "slug"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with this {field} already exists.",
        )

    category = Category(
        name=data.name,
        slug=data.slug,
        description=data.description,
        image_url=data.image_url,
    )
    db.add(category)
    await db.flush()

    return CategoryResponse.model_validate(category)


async def list_categories_admin(
    db: AsyncSession,
    search: str | None,
    status_filter: str | None,
    page: int,
    limit: int,
) -> CategoryListResponse:
    query = select(Category)

    if search is not None:
        term = f"%{search}%"
        query = query.where(
            or_(
                Category.name.ilike(term),
                Category.slug.ilike(term),
            )
        )

    if status_filter == "active":
        query = query.where(Category.is_active == True)  # noqa: E712
    elif status_filter == "inactive":
        query = query.where(Category.is_active == False)  # noqa: E712

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Category.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    categories = result.scalars().all()

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(c) for c in categories],
        total=total,
        page=page,
        limit=limit,
    )


async def list_categories_public(
    db: AsyncSession,
    page: int,
    limit: int,
) -> CategoryListResponse:
    query = select(Category).where(Category.is_active == True)  # noqa: E712

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(Category.name.asc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    categories = result.scalars().all()

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(c) for c in categories],
        total=total,
        page=page,
        limit=limit,
    )


async def update_category(
    db: AsyncSession,
    category_id: str,
    data: CategoryUpdateRequest,
) -> CategoryResponse:
    category = await _get_category_by_id(db, category_id)

    if data.name is not None:
        existing = await db.scalar(
            select(Category).where(Category.name == data.name)
        )
        if existing is not None and str(existing.id) != str(category.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists.",
            )
        category.name = data.name

    if data.slug is not None:
        existing = await db.scalar(
            select(Category).where(Category.slug == data.slug)
        )
        if existing is not None and str(existing.id) != str(category.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this slug already exists.",
            )
        category.slug = data.slug

    if data.description is not None:
        category.description = data.description

    if data.image_url is not None:
        category.image_url = data.image_url

    if data.is_active is not None:
        category.is_active = data.is_active

    await db.flush()

    return CategoryResponse.model_validate(category)


async def delete_category(
    db: AsyncSession,
    category_id: str,
) -> None:
    category = await _get_category_by_id(db, category_id)

    if not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category is already inactive.",
        )

    category.is_active = False


async def _get_category_by_id(
    db: AsyncSession,
    category_id: str,
) -> Category:
    import uuid
    uid = uuid.UUID(str(category_id))
    stmt = select(Category).where(Category.id == uid)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    return category