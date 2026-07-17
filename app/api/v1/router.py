from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.cart import router as cart_router
from app.api.v1.category import router as category_router
from app.api.v1.order import router as order_router
from app.api.v1.payment import router as payment_router
from app.api.v1.product import router as product_router
from app.api.v1.seller import router as seller_router
from app.api.v1.admin import router as admin_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(category_router)
v1_router.include_router(product_router)
v1_router.include_router(cart_router)
v1_router.include_router(order_router)
v1_router.include_router(payment_router)
v1_router.include_router(seller_router)
v1_router.include_router(admin_router)