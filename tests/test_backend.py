import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_and_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_root = await ac.get("/")
        assert res_root.status_code == 200
        assert res_root.json()["status"] == "running"

        res_health = await ac.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_full_auth_and_ecommerce_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        import uuid
        uid = uuid.uuid4().hex[:6]

        # 1. Login Admin (seeded default admin)
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@gmail.com",
            "password": "Admin@123"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create Category via Admin
        cat_res = await ac.post("/api/v1/admin/categories", json={
            "name": f"Electronics_{uid}",
            "slug": f"electronics-{uid}",
            "description": "Tech gadgets"
        }, headers=admin_headers)
        assert cat_res.status_code == 201
        cat_id = cat_res.json()["id"]

        # 3. Register Seller
        seller_email = f"seller_{uid}@test.com"
        reg_seller = await ac.post("/api/v1/auth/register", json={
            "full_name": "Test Seller",
            "email": seller_email,
            "password": "Password@123",
            "role": "seller",
            "business_name": "Test Store"
        })
        assert reg_seller.status_code == 201
        seller_id = reg_seller.json()["user"]["id"]
        seller_token = reg_seller.json()["access_token"]

        # 4. Admin Approves Seller
        appr_res = await ac.post(f"/api/v1/admin/sellers/{seller_id}/approve", headers=admin_headers)
        assert appr_res.status_code == 200

        # Seller re-logins to get refreshed token with APPROVED status
        seller_login = await ac.post("/api/v1/auth/login", json={
            "email": seller_email,
            "password": "Password@123"
        })
        assert seller_login.status_code == 200
        seller_token = seller_login.json()["access_token"]
        seller_headers = {"Authorization": f"Bearer {seller_token}"}

        # 5. Create Product via Seller
        prod_res = await ac.post("/api/v1/seller/products", json={
            "name": f"Wireless Headphones_{uid}",
            "description": "Noise cancelling headphones",
            "price": 1999.00,
            "stock": 50,
            "category_id": cat_id,
            "image_url": "https://example.com/item.jpg"
        }, headers=seller_headers)
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        # 6. Register Customer
        cust_email = f"customer_{uid}@test.com"
        reg_cust = await ac.post("/api/v1/auth/register", json={
            "full_name": "Test Customer",
            "email": cust_email,
            "password": "Password@123",
            "role": "customer"
        })
        assert reg_cust.status_code == 201
        cust_token = reg_cust.json()["access_token"]
        cust_headers = {"Authorization": f"Bearer {cust_token}"}

        # 7. Add Product to Cart
        cart_res = await ac.post("/api/v1/cart", json={
            "product_id": prod_id,
            "quantity": 2
        }, headers=cust_headers)
        assert cart_res.status_code in (200, 201)

        # 8. Place Order & Create Razorpay Order
        order_res = await ac.post("/api/v1/orders", json={
            "seller_id": seller_id,
            "shipping_address": {
                "full_name": "Test Customer",
                "phone": "9876543210",
                "address_line_1": "123 Main St",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
                "country": "India"
            }
        }, headers=cust_headers)
        assert order_res.status_code == 201
        order_data = order_res.json()
        assert "razorpay_order_id" in order_data
        razorpay_order_id = order_data["razorpay_order_id"]

        # 9. Verify Razorpay Payment Signature
        pay_res = await ac.post("/api/v1/payments/verify", json={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "razorpay_signature": "dummy_sig_test_mode"
        }, headers=cust_headers)
        assert pay_res.status_code == 200
        assert pay_res.json()["message"] == "Payment verified successfully"

        # 10. Razorpay Webhook Event Handling
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
