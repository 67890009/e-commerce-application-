from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentVerifyResponse, VerifyPaymentRequest
from app.services import payment as payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/verify",
    response_model=PaymentVerifyResponse,
)
async def verify_payment(
    body: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentVerifyResponse:
    return await payment_service.verify_payment(
        db=db,
        data=body,
    )


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
) -> dict[str, str]:
    payload_bytes = await request.body()
    return await payment_service.handle_razorpay_webhook(
        db=db,
        payload_bytes=payload_bytes,
        signature=x_razorpay_signature,
    )