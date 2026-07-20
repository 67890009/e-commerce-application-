from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart_item import CartItem
from app.models.order import Order, OrderItem, OrderStatus, VALID_TRANSITIONS
from app.models.product import Product, ProductStatus
from app.schemas.order import (
    CreateOrderRequest,
    CreateOrderResponse,
    OrderDetailResponse,
    OrderItemResponse,
    OrderListItemResponse,
    OrderListResponse,
    OrderStatusUpdateResponse,
    ShippingAddressSchema,
)
from app.dependencies.cart import CartIdentity


# ── Customer ────────────────────────────────────────────────────


async def create_order(
    db: AsyncSession,
    user_id: str,
    data: CreateOrderRequest,
    identity: CartIdentity,
) -> CreateOrderResponse:
    from app.services.payment import create_razorpay_order

    seller_id = str(data.seller_id)

    # Fetch cart items for this seller
    if identity.user_id is not None:
        stmt = select(CartItem).where(
            CartItem.user_id == identity.user_id,
            CartItem.product_id.in_(
                select(Product.id).where(Product.seller_id == seller_id)
            ),
        )
    else:
        stmt = select(CartItem).where(
            CartItem.cart_token == identity.cart_token,
            CartItem.user_id.is_(None),
            CartItem.product_id.in_(
                select(Product.id).where(Product.seller_id == seller_id)
            ),
        )

    result = await db.execute(stmt)
    cart_items = list(result.scalars().all())

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items in cart for this seller.",
        )

    # Validate stock and build order items
    order_items_data = []
    total_amount = Decimal("0")

    for ci in cart_items:
        product = ci.product
        if product.stock < ci.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}",
            )
        subtotal = Decimal(str(product.price)) * ci.quantity
        order_items_data.append(
            {
                "product_id": str(product.id),
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image_url,
                "quantity": ci.quantity,
                "subtotal": subtotal,
            }
        )
        total_amount += subtotal

    # Create order
    order = Order(
        user_id=user_id,
        seller_id=seller_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING.value,
        shipping_address=data.shipping_address.model_dump(),
    )
    db.add(order)
    await db.flush()

    # Create order items
    for item_data in order_items_data:
        oi = OrderItem(order_id=str(order.id), **item_data)
        db.add(oi)

    # Deduct stock
    for ci in cart_items:
        await db.execute(
            update(Product)
            .where(Product.id == ci.product_id)
            .values(stock=Product.stock - ci.quantity)
        )

    # Remove cart items
    for ci in cart_items:
        await db.delete(ci)

    await db.flush()

    # Create Razorpay order
    razorpay_order_id = await create_razorpay_order(
        db=db,
        order_id=str(order.id),
        amount=total_amount,
    )

    order_detail = await _build_detail_response(db, order)

    return CreateOrderResponse(
        order=order_detail,
        razorpay_order_id=razorpay_order_id,
    )


async def list_my_orders(
    db: AsyncSession,
    user_id: str,
    page: int,
    limit: int,
) -> OrderListResponse:
    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return OrderListResponse(
        orders=[_build_list_item(o) for o in orders],
        total=total,
        page=page,
        limit=limit,
    )


async def get_my_order(
    db: AsyncSession,
    user_id: str,
    order_id: str,
) -> OrderDetailResponse:
    order = await _get_order_by_id(db, order_id)
    if str(order.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    return await _build_detail_response(db, order)


# ── Seller ──────────────────────────────────────────────────────


async def list_seller_orders(
    db: AsyncSession,
    seller_id: str,
    status_filter: str | None,
    page: int,
    limit: int,
) -> OrderListResponse:
    query = select(Order).where(Order.seller_id == seller_id)

    if status_filter is not None:
        query = query.where(Order.status == status_filter)

    query = query.order_by(Order.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return OrderListResponse(
        orders=[_build_seller_list_item(o) for o in orders],
        total=total,
        page=page,
        limit=limit,
    )


async def get_seller_order(
    db: AsyncSession,
    seller_id: str,
    order_id: str,
) -> OrderDetailResponse:
    order = await _get_order_by_id(db, order_id)
    if str(order.seller_id) != str(seller_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    return await _build_detail_response(db, order)


# ── Admin ───────────────────────────────────────────────────────


async def list_orders_admin(
    db: AsyncSession,
    status_filter: str | None,
    user_id: str | None,
    search: str | None,
    page: int,
    limit: int,
) -> OrderListResponse:
    query = select(Order)

    if status_filter is not None:
        query = query.where(Order.status == status_filter)

    if user_id is not None:
        query = query.where(Order.user_id == user_id)

    if search is not None:
        term = f"%{search}%"
        query = query.where(Order.id.ilike(term))

    query = query.order_by(Order.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return OrderListResponse(
        orders=[_build_admin_list_item(o) for o in orders],
        total=total,
        page=page,
        limit=limit,
    )


async def get_order_admin(
    db: AsyncSession,
    order_id: str,
) -> OrderDetailResponse:
    order = await _get_order_by_id(db, order_id)
    return await _build_detail_response(db, order)


async def update_order_status(
    db: AsyncSession,
    order_id: str,
    new_status: str,
) -> OrderStatusUpdateResponse:
    order = await _get_order_by_id(db, order_id)

    allowed = VALID_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{order.status}' to '{new_status}'.",
        )

    old_status = order.status
    order.status = new_status

    if new_status == OrderStatus.CANCELLED.value:
        await _restore_stock(db, order)

    await db.flush()

    return OrderStatusUpdateResponse(
        message=f"Order status updated from '{old_status}' to '{new_status}'",
        order_id=order.id,
        status=new_status,
    )


# ── Internal ────────────────────────────────────────────────────


async def _get_order_by_id(
    db: AsyncSession,
    order_id: str,
) -> Order:
    import uuid
    uid = uuid.UUID(str(order_id))
    stmt = select(Order).where(Order.id == uid)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return order


async def _build_detail_response(
    db: AsyncSession,
    order: Order,
) -> OrderDetailResponse:
    items_stmt = (
        select(OrderItem)
        .where(OrderItem.order_id == str(order.id))
        .order_by(OrderItem.created_at.asc())
    )
    items_result = await db.execute(items_stmt)
    items = items_result.scalars().all()

    return OrderDetailResponse(
        id=order.id,
        user_id=order.user_id,
        customer_name=order.user.full_name,
        customer_email=order.user.email,
        seller_id=order.seller_id,
        seller_name=order.seller.full_name,
        seller_business_name=order.seller.business_name,
        total_amount=order.total_amount,
        status=order.status,
        shipping_address=ShippingAddressSchema(**order.shipping_address),
        items=[OrderItemResponse.model_validate(i) for i in items],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _build_list_item(order: Order) -> OrderListItemResponse:
    return OrderListItemResponse(
        id=order.id,
        seller_id=order.seller_id,
        seller_name=order.seller.full_name,
        seller_business_name=order.seller.business_name,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )


def _build_seller_list_item(order: Order) -> OrderListItemResponse:
    return OrderListItemResponse(
        id=order.id,
        seller_id=order.seller_id,
        seller_name=order.user.full_name,
        seller_business_name=None,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )


def _build_admin_list_item(order: Order) -> OrderListItemResponse:
    return OrderListItemResponse(
        id=order.id,
        seller_id=order.seller_id,
        seller_name=order.seller.full_name,
        seller_business_name=order.seller.business_name,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )


async def _restore_stock(
    db: AsyncSession,
    order: Order,
) -> None:
    stmt = select(OrderItem).where(OrderItem.order_id == str(order.id))
    result = await db.execute(stmt)
    items = result.scalars().all()

    for item in items:
        await db.execute(
            update(Product)
            .where(Product.id == item.product_id)
            .values(stock=Product.stock + item.quantity)
        )