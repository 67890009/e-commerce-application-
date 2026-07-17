from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str | None
    amount: Decimal
    currency: str
    status: str
    platform_commission: Decimal
    seller_payout_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentVerifyResponse(BaseModel):
    message: str
    payment: PaymentResponse