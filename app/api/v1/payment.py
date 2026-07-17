from fastapi import APIRouter, Depends
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