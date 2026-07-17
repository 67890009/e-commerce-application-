from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.cart import CartIdentity, get_cart_identity
from app.models.user import User
from app.schemas.order import (
    CreateOrderRequest,
    CreateOrderResponse,
    OrderDetailResponse,
    OrderListResponse,
)
from app.services import order as order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=CreateOrderResponse,
    status_code=201,
)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    identity: CartIdentity = Depends(get_cart_identity),
) -> CreateOrderResponse:
    return await order_service.create_order(
        db=db,
        user_id=str(user.id),
        data=body,
        identity=identity,
    )


@router.get(
    "",
    response_model=OrderListResponse,
)
async def list_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderListResponse:
    return await order_service.list_my_orders(
        db=db,
        user_id=str(user.id),
        page=page,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
)
async def get_my_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailResponse:
    return await order_service.get_my_order(
        db=db,
        user_id=str(user.id),
        order_id=order_id,
    )