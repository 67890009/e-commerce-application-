# Import all models here so Alembic can auto-detect them.
# Every new model file MUST be added to this list.

from app.models.base import Base
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.google_auth_code import GoogleAuthCode

__all__ = [
    "Base",
    "User",
    "RefreshToken",
    "GoogleAuthCode",
]