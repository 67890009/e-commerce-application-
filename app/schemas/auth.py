import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic import ConfigDict


# ── Password Validation Constants ───────────────────────────────

_SPECIAL_CHARS = r"!@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"


# ── Requests ────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["customer", "seller"]

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number.")
        if not any(c in _SPECIAL_CHARS for c in v):
            raise ValueError(
                "Password must contain at least one special character."
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class GoogleExchangeRequest(BaseModel):
    code: str


# ── Responses ───────────────────────────────────────────────────


class UserResponse(BaseModel):
    """Represents the user object returned inside auth responses and /me."""

    id: UUID
    full_name: str
    email: str
    role: str
    seller_approved: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """
    Returned by register, login, and Google exchange.
    Same shape for all three — frontend handles them identically.
    """

    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshResponse(BaseModel):
    """Returned by the refresh endpoint. No user object — just new tokens."""

    access_token: str
    refresh_token: str
    expires_in: int