import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.user import User

async def seed():
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == 'admin@marketplace.com')
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print('Admin already exists')
            return

        admin = User(
            full_name='Admin',
            email='admin@marketplace.com',
            hashed_password=hash_password('Admin@123'),
            role='admin',
            seller_status=None,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f'Admin created: {admin.email} / Admin@123')

asyncio.run(seed())
