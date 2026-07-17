from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.cart import CartIdentity, get_cart_identity
from app.models.user import User
from app.schemas.cart import (
    AddToCartRequest,
    CartItemResponse,
    CartResponse,
    MergeCartRequest,
    MergeCartResponse,
    UpdateQuantityRequest,
)
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post(
    "",
    response_model=CartItemResponse,
    status_code=201,
)
async def add_to_cart(
    body: AddToCartRequest,
    db: AsyncSession = Depends(get_db),
    identity: CartIdentity = Depends(get_cart_identity),
) -> CartItemResponse:
    return await cart_service.add_to_cart(
        db=db,
        identity=identity,
        data=body,
    )


@router.get(
    "",
    response_model=CartResponse,
)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    identity: CartIdentity = Depends(get_cart_identity),
) -> CartResponse:
    return await cart_service.get_cart(db=db, identity=identity)


@router.patch(
    "/items/{item_id}",
    response_model=CartItemResponse,
)
async def update_quantity(
    item_id: str,
    body: UpdateQuantityRequest,
    db: AsyncSession = Depends(get_db),
    identity: CartIdentity = Depends(get_cart_identity),
) -> CartItemResponse:
    return await cart_service.update_quantity(
        db=db,
        identity=identity,
        item_id=item_id,
        data=body,
    )


@router.delete(
    "/items/{item_id}",
    status_code=204,
)
async def remove_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    identity: CartIdentity = Depends(get_cart_identity),
) -> None:
    await cart_service.remove_item(
        db=db,
        identity=identity,
        item_id=item_id,
    )


@router.delete(
    "",
    status_code=204,
)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    identity: CartIdentity = Depends(get_cart_identity),
) -> None:
    await cart_service.clear_cart(db=db, identity=identity)


@router.post(
    "/merge",
    response_model=MergeCartResponse,
)
async def merge_cart(
    body: MergeCartRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MergeCartResponse:
    return await cart_service.merge_cart(
        db=db,
        user_id=str(user.id),
        cart_token=body.cart_token,
    )