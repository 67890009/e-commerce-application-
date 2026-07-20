import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_every_single_api_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        suffix = uuid.uuid4().hex[:6]

        # ────────────────────────────────────────────────────────────
        # 1. AUTH & GOOGLE OAUTH ENDPOINTS
        # ────────────────────────────────────────────────────────────
        
        # Test Google OAuth Login Redirect URL generator endpoint
        google_login_res = await ac.get("/api/v1/auth/google/login", follow_redirects=False)
        assert google_login_res.status_code == 307
        assert "accounts.google.com" in google_login_res.headers["location"]

        # Test Google OAuth Code Exchange
        from app.models.google_auth_code import GoogleAuthCode
        from app.models.user import User
        from app.core.security import generate_oauth_code, hash_oauth_code
        from app.core.database import async_session_factory as AsyncSessionLocal
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select

        raw_test_code = generate_oauth_code()
        hashed_test_code = hash_oauth_code(raw_test_code)
        async with AsyncSessionLocal() as db_sess:
            u_res = await db_sess.execute(select(User).where(User.email == "admin@gmail.com"))
            admin_user_rec = u_res.scalar_one()
            db_sess.add(GoogleAuthCode(
                code_hash=hashed_test_code,
                user_id=admin_user_rec.id,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=60)
            ))
            await db_sess.commit()

        google_ex_res = await ac.post("/api/v1/auth/google/exchange", json={"code": raw_test_code})
        assert google_ex_res.status_code == 200
        assert "access_token" in google_ex_res.json()

        # Admin Login (seeded default super-admin)
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@gmail.com",
            "password": "Admin@123"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Auth /me endpoint for Admin
        admin_me = await ac.get("/api/v1/auth/me", headers=admin_headers)
        assert admin_me.status_code == 200
        assert admin_me.json()["email"] == "admin@gmail.com"

        # Register Seller 1
        seller_email = f"seller1_{suffix}@test.com"
        reg_seller = await ac.post("/api/v1/auth/register", json={
            "full_name": "Seller One",
            "email": seller_email,
            "password": "Password@123",
            "role": "seller",
            "business_name": "Electronics Hub"
        })
        assert reg_seller.status_code == 201
        seller_id = reg_seller.json()["user"]["id"]
        seller_token = reg_seller.json()["access_token"]
        seller_refresh_token = reg_seller.json()["refresh_token"]

        # Register Seller 2 (for testing reject/suspend/ban admin endpoints)
        seller2_email = f"seller2_{suffix}@test.com"
        reg_seller2 = await ac.post("/api/v1/auth/register", json={
            "full_name": "Seller Two",
            "email": seller2_email,
            "password": "Password@123",
            "role": "seller",
            "business_name": "Store Two"
        })
        assert reg_seller2.status_code == 201
        seller2_id = reg_seller2.json()["user"]["id"]

        # Test Refresh Token endpoint
        refresh_res = await ac.post("/api/v1/auth/refresh", json={
            "refresh_token": seller_refresh_token
        })
        assert refresh_res.status_code == 200
        assert "access_token" in refresh_res.json()

        # Register Customer
        cust_email = f"cust_{suffix}@test.com"
        reg_cust = await ac.post("/api/v1/auth/register", json={
            "full_name": "Customer One",
            "email": cust_email,
            "password": "Password@123",
            "role": "customer"
        })
        assert reg_cust.status_code == 201
        cust_token = reg_cust.json()["access_token"]
        cust_headers = {"Authorization": f"Bearer {cust_token}"}

        # ────────────────────────────────────────────────────────────
        # 2. ADMIN SELLER MANAGEMENT ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # List sellers
        sellers_list = await ac.get("/api/v1/admin/sellers", headers=admin_headers)
        assert sellers_list.status_code == 200
        assert sellers_list.json()["total"] >= 2

        # Get seller detail
        seller_detail = await ac.get(f"/api/v1/admin/sellers/{seller_id}", headers=admin_headers)
        assert seller_detail.status_code == 200
        assert seller_detail.json()["email"] == seller_email

        # Approve Seller 1
        appr_res = await ac.post(f"/api/v1/admin/sellers/{seller_id}/approve", headers=admin_headers)
        assert appr_res.status_code == 200
        assert appr_res.json()["seller_status"] == "approved"

        # Suspend & Reinstate Seller 2
        appr_s2 = await ac.post(f"/api/v1/admin/sellers/{seller2_id}/approve", headers=admin_headers)
        assert appr_s2.status_code == 200
        susp_res = await ac.post(f"/api/v1/admin/sellers/{seller2_id}/suspend", json={"reason": "Policy violation test"}, headers=admin_headers)
        assert susp_res.status_code == 200
        rein_res = await ac.post(f"/api/v1/admin/sellers/{seller2_id}/reinstate", headers=admin_headers)
        assert rein_res.status_code == 200

        # Seller 1 Re-login after approval
        seller_login = await ac.post("/api/v1/auth/login", json={
            "email": seller_email,
            "password": "Password@123"
        })
        assert seller_login.status_code == 200
        seller_token = seller_login.json()["access_token"]
        seller_headers = {"Authorization": f"Bearer {seller_token}"}

        # ────────────────────────────────────────────────────────────
        # 3. ADMIN & PUBLIC CATEGORIES ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # Create Category (Admin)
        cat_res = await ac.post("/api/v1/admin/categories", json={
            "name": f"Gadgets_{suffix}",
            "slug": f"gadgets-{suffix}",
            "description": "Smart gadgets and devices"
        }, headers=admin_headers)
        assert cat_res.status_code == 201
        cat_id = cat_res.json()["id"]

        # List categories (Admin)
        cat_admin_list = await ac.get("/api/v1/admin/categories", headers=admin_headers)
        assert cat_admin_list.status_code == 200

        # Update category (Admin)
        cat_upd = await ac.patch(f"/api/v1/admin/categories/{cat_id}", json={
            "description": "Updated tech gadgets description"
        }, headers=admin_headers)
        assert cat_upd.status_code == 200

        # Public categories list
        pub_cats = await ac.get("/api/v1/categories")
        assert pub_cats.status_code == 200

        # ────────────────────────────────────────────────────────────
        # 4. SELLER & PUBLIC PRODUCTS ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # Create Product (Seller)
        prod_res = await ac.post("/api/v1/seller/products", json={
            "name": f"Smartwatch Pro_{suffix}",
            "description": "Fitness tracking smartwatch",
            "price": 2999.00,
            "stock": 100,
            "category_id": cat_id,
            "image_url": "https://example.com/watch.jpg"
        }, headers=seller_headers)
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        # List Seller products
        seller_prods = await ac.get("/api/v1/seller/products", headers=seller_headers)
        assert seller_prods.status_code == 200

        # Get Seller product detail
        seller_pdetail = await ac.get(f"/api/v1/seller/products/{prod_id}", headers=seller_headers)
        assert seller_pdetail.status_code == 200

        # Update Seller product
        seller_pupd = await ac.patch(f"/api/v1/seller/products/{prod_id}", json={
            "stock": 80
        }, headers=seller_headers)
        assert seller_pupd.status_code == 200
        assert seller_pupd.json()["stock"] == 80

        # Public list products & Public product detail
        pub_prods = await ac.get("/api/v1/products")
        assert pub_prods.status_code == 200
        
        pub_pdetail = await ac.get(f"/api/v1/products/{prod_id}")
        assert pub_pdetail.status_code == 200
        assert pub_pdetail.json()["name"] == f"Smartwatch Pro_{suffix}"

        # ────────────────────────────────────────────────────────────
        # 5. CART ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # Add to cart
        cart_add = await ac.post("/api/v1/cart", json={
            "product_id": prod_id,
            "quantity": 3
        }, headers=cust_headers)
        assert cart_add.status_code == 201
        cart_item_id = cart_add.json()["id"]

        # Get cart
        cart_get = await ac.get("/api/v1/cart", headers=cust_headers)
        assert cart_get.status_code == 200
        assert cart_get.json()["total_items"] == 3

        # Update cart item quantity
        cart_upd = await ac.patch(f"/api/v1/cart/items/{cart_item_id}", json={
            "quantity": 2
        }, headers=cust_headers)
        assert cart_upd.status_code == 200
        assert cart_upd.json()["quantity"] == 2

        # ────────────────────────────────────────────────────────────
        # 6. ORDERS & RAZORPAY PAYMENT ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # Create Order
        order_res = await ac.post("/api/v1/orders", json={
            "seller_id": seller_id,
            "shipping_address": {
                "full_name": "Customer One",
                "phone": "9876543210",
                "address_line_1": "Flat 402, Green Towers",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "country": "India"
            }
        }, headers=cust_headers)
        assert order_res.status_code == 201
        order_id = order_res.json()["order"]["id"]
        razorpay_order_id = order_res.json()["razorpay_order_id"]

        # Customer List My Orders & Get Order Detail
        my_orders = await ac.get("/api/v1/orders", headers=cust_headers)
        assert my_orders.status_code == 200
        assert my_orders.json()["total"] >= 1

        my_order_detail = await ac.get(f"/api/v1/orders/{order_id}", headers=cust_headers)
        assert my_order_detail.status_code == 200

        # Seller List Seller Orders & Get Seller Order Detail
        seller_orders = await ac.get("/api/v1/seller/orders", headers=seller_headers)
        assert seller_orders.status_code == 200
        assert seller_orders.json()["total"] >= 1

        seller_order_detail = await ac.get(f"/api/v1/seller/orders/{order_id}", headers=seller_headers)
        assert seller_order_detail.status_code == 200

        # Verify Payment
        verify_pay = await ac.post("/api/v1/payments/verify", json={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "razorpay_signature": "dummy_sig_test_mode"
        }, headers=cust_headers)
        assert verify_pay.status_code == 200
        assert verify_pay.json()["message"] == "Payment verified successfully"

        # Razorpay Webhook Event
        webhook_res = await ac.post("/api/v1/payments/webhook", json={
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4().hex[:12]}",
                        "order_id": razorpay_order_id
                    }
                }
            }
        })
        assert webhook_res.status_code == 200
        assert webhook_res.json() == {"status": "ok"}

        # ────────────────────────────────────────────────────────────
        # 7. ADMIN ORDERS, DASHBOARD & PRODUCT CONTROL ENDPOINTS
        # ────────────────────────────────────────────────────────────

        # Admin List Orders & Get Order Detail
        admin_orders = await ac.get("/api/v1/admin/orders", headers=admin_headers)
        assert admin_orders.status_code == 200

        admin_order_detail = await ac.get(f"/api/v1/admin/orders/{order_id}", headers=admin_headers)
        assert admin_order_detail.status_code == 200

        # Admin Update Order Status (transition from confirmed to shipped)
        order_stat_upd = await ac.patch(f"/api/v1/admin/orders/{order_id}/status", json={
            "status": "shipped"
        }, headers=admin_headers)
        print("DEBUG ORDER STATUS UPDATE:", order_stat_upd.status_code, order_stat_upd.text)
        assert order_stat_upd.status_code == 200
        assert order_stat_upd.json()["status"] == "shipped"

        # Admin Products List & Detail
        admin_prods = await ac.get("/api/v1/admin/products", headers=admin_headers)
        assert admin_prods.status_code == 200

        admin_pdetail = await ac.get(f"/api/v1/admin/products/{prod_id}", headers=admin_headers)
        assert admin_pdetail.status_code == 200

        # Admin Disable & Enable Product
        dis_res = await ac.post(f"/api/v1/admin/products/{prod_id}/disable", json={"reason": "Testing disable"}, headers=admin_headers)
        assert dis_res.status_code == 200
        en_res = await ac.post(f"/api/v1/admin/products/{prod_id}/enable", headers=admin_headers)
        assert en_res.status_code == 200

        # Admin Dashboard Stats
        dash_res = await ac.get("/api/v1/admin/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        assert dash_res.json()["total_sellers"] >= 1

        # Logout Customer
        logout_res = await ac.post("/api/v1/auth/logout", json={"refresh_token": seller_refresh_token}, headers=seller_headers)
        assert logout_res.status_code == 204
