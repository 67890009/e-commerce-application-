from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart_item import CartItem
from app.models.product import Product, ProductStatus
from app.schemas.cart import (
    AddToCartRequest,
    CartItemResponse,
    CartResponse,
    MergeCartResponse,
    UpdateQuantityRequest,
)
from app.dependencies.cart import CartIdentity


async def add_to_cart(
    db: AsyncSession,
    identity: CartIdentity,
    data: AddToCartRequest,
) -> CartItemResponse:
    product = await _get_active_product(db, str(data.product_id))

    if product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock.",
        )

    existing = await _find_existing_item(
        db, identity, str(data.product_id)
    )

    if existing is not None:
        new_qty = existing.quantity + data.quantity
        if product.stock < new_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock.",
            )
        existing.quantity = new_qty
        await db.flush()
        return _build_item_response(existing)

    item = CartItem(
        cart_token=identity.cart_token,
        user_id=identity.user_id,
        product_id=str(data.product_id),
        quantity=data.quantity,
    )
    db.add(item)
    await db.flush()
    return _build_item_response(item)


async def get_cart(
    db: AsyncSession,
    identity: CartIdentity,
) -> CartResponse:
    items = await _get_cart_items(db, identity)
    total_items = sum(i.quantity for i in items)
    total_amount = sum(
        i.quantity * i.product.price for i in items
    )
    return CartResponse(
        items=[_build_item_response(i) for i in items],
        total_items=total_items,
        total_amount=total_amount,
    )


async def update_quantity(
    db: AsyncSession,
    identity: CartIdentity,
    item_id: str,
    data: UpdateQuantityRequest,
) -> CartItemResponse:
    item = await _get_cart_item_owned(db, identity, item_id)

    if item.product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock.",
        )

    item.quantity = data.quantity
    await db.flush()
    return _build_item_response(item)


async def remove_item(
    db: AsyncSession,
    identity: CartIdentity,
    item_id: str,
) -> None:
    item = await _get_cart_item_owned(db, identity, item_id)
    await db.delete(item)


async def clear_cart(
    db: AsyncSession,
    identity: CartIdentity,
) -> None:
    if identity.user_id is not None:
        await db.execute(
            delete(CartItem).where(CartItem.user_id == identity.user_id)
        )
    else:
        await db.execute(
            delete(CartItem).where(CartItem.cart_token == identity.cart_token)
        )


async def merge_cart(
    db: AsyncSession,
    user_id: str,
    cart_token: str,
) -> MergeCartResponse:
    stmt = select(CartItem).where(
        CartItem.cart_token == cart_token,
        CartItem.user_id.is_(None),
    )
    result = await db.execute(stmt)
    guest_items = result.scalars().all()

    merged_count = 0

    for guest_item in guest_items:
        existing = await db.scalar(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == guest_item.product_id,
            )
        )

        if existing is not None:
            existing.quantity += guest_item.quantity
            await db.delete(guest_item)
        else:
            guest_item.user_id = user_id
            guest_item.cart_token = None
            merged_count += 1

    await db.flush()

    total_stmt = select(CartItem).where(CartItem.user_id == user_id)
    total_result = await db.execute(total_stmt)
    total_items = len(total_result.scalars().all())

    return MergeCartResponse(
        message="Cart merged",
        items_count=total_items,
    )


# ── Internal ────────────────────────────────────────────────────


async def _get_active_product(
    db: AsyncSession,
    product_id: str,
) -> Product:
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

    return product


async def _find_existing_item(
    db: AsyncSession,
    identity: CartIdentity,
    product_id: str,
) -> CartItem | None:
    if identity.user_id is not None:
        stmt = select(CartItem).where(
            CartItem.user_id == identity.user_id,
            CartItem.product_id == product_id,
        )
    else:
        stmt = select(CartItem).where(
            CartItem.cart_token == identity.cart_token,
            CartItem.user_id.is_(None),
            CartItem.product_id == product_id,
        )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_cart_items(
    db: AsyncSession,
    identity: CartIdentity,
) -> list[CartItem]:
    if identity.user_id is not None:
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == identity.user_id)
            .order_by(CartItem.created_at.desc())
        )
    else:
        stmt = (
            select(CartItem)
            .where(
                CartItem.cart_token == identity.cart_token,
                CartItem.user_id.is_(None),
            )
            .order_by(CartItem.created_at.desc())
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_cart_item_owned(
    db: AsyncSession,
    identity: CartIdentity,
    item_id: str,
) -> CartItem:
    if identity.user_id is not None:
        stmt = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.user_id == identity.user_id,
        )
    else:
        stmt = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_token == identity.cart_token,
            CartItem.user_id.is_(None),
        )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )

    return item


def _build_item_response(item: CartItem) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        product_id=item.product.id,
        product_name=item.product.name,
        product_price=item.product.price,
        product_image=item.product.image_url,
        product_stock=item.product.stock,
        seller_id=item.product.seller_id,
        quantity=item.quantity,
        created_at=item.created_at,
    )