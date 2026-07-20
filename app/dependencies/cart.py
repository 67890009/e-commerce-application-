from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


class CartIdentity:
    def __init__(self, user_id: str | None, cart_token: str | None):
        self.user_id = user_id
        self.cart_token = cart_token


async def get_optional_bearer(
    authorization: str | None = Header(None),
) -> dict | None:
    if authorization is None:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    return {"token": token}


async def get_current_user_optional(
    credentials: dict | None = Depends(get_optional_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None

    payload = decode_access_token(credentials["token"])
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    import uuid
    uid = uuid.UUID(str(user_id))
    stmt = select(User).where(User.id == uid, User.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_cart_identity(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_cart_token: str | None = Header(None, alias="X-Cart-Token"),
) -> CartIdentity:
    if user is not None:
        return CartIdentity(user_id=str(user.id), cart_token=None)

    if x_cart_token is not None:
        return CartIdentity(user_id=None, cart_token=x_cart_token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Bearer token or X-Cart-Token header.",
    )