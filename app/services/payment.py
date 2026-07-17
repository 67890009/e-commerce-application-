from __future__ import annotations

import hashlib
import hmac
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentResponse, PaymentVerifyResponse, VerifyPaymentRequest


async def create_razorpay_order(
    db: AsyncSession,
    order_id: str,
    amount: Decimal,
) -> str:
    """
    Create a Razorpay order.
    In test mode, returns a placeholder ID.
    In production, calls the Razorpay API.
    Returns the razorpay_order_id.
    """
    if settings.RAZORPAY_TEST_MODE:
        razorpay_order_id = f"rzp_test_{uuid.uuid4().hex[:20]}"
    else:
        try:
            import razorpay

            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            order_data = {
                "amount": int(amount * 100),  # Razorpay expects paise
                "currency": "INR",
                "receipt": str(order_id),
                "timeout": settings.PAYMENT_TIMEOUT_MINUTES * 60,
            }
            razorpay_order = client.order.create(data=order_data)
            razorpay_order_id = razorpay_order["id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create payment order: {str(e)}",
            )

    # Calculate commission and payout
    commission = amount * (Decimal(str(settings.PLATFORM_COMMISSION_PERCENTAGE)) / Decimal("100"))
    payout = amount - commission

    # Create payment record
    payment = Payment(
        order_id=order_id,
        razorpay_order_id=razorpay_order_id,
        amount=amount,
        platform_commission=commission,
        seller_payout_amount=payout,
        status=PaymentStatus.CREATED.value,
    )
    db.add(payment)
    await db.flush()

    return razorpay_order_id


async def verify_payment(
    db: AsyncSession,
    data: VerifyPaymentRequest,
) -> PaymentVerifyResponse:
    """
    Verify Razorpay payment signature.
    In test mode, always succeeds.
    In production, verifies HMAC-SHA256.
    """
    # Fetch payment record
    stmt = select(Payment).where(
        Payment.razorpay_order_id == data.razorpay_order_id
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )

    if payment.status == PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already verified.",
        )

    # Verify signature
    if settings.RAZORPAY_TEST_MODE:
        is_valid = True
    else:
        message = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(
            expected_signature, data.razorpay_signature
        )

    if not is_valid:
        payment.status = PaymentStatus.FAILED.value
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature.",
        )

    # Mark as paid
    payment.status = PaymentStatus.PAID.value
    payment.razorpay_payment_id = data.razorpay_payment_id
    payment.razorpay_signature = data.razorpay_signature

    # Update order status to confirmed
    order_stmt = select(Order).where(Order.id == payment.order_id)
    order_result = await db.execute(order_stmt)
    order = order_result.scalar_one_or_none()

    if order is not None and order.status == OrderStatus.PENDING.value:
        order.status = OrderStatus.CONFIRMED.value

    await db.flush()

    return PaymentVerifyResponse(
        message="Payment verified successfully",
        payment=PaymentResponse.model_validate(payment),
    )