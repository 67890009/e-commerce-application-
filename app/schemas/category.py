import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(None, max_length=120)

    @field_validator("slug")
    @classmethod
    def auto_generate_slug(cls, v: str | None, info) -> str | None:
        if v is not None and v.strip():
            return _generate_slug(v)
        # Generate from name
        name = info.data.get("name")
        if name:
            return _generate_slug(name)
        return None


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, max_length=120)
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def sanitize_slug(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            return _generate_slug(v)
        return None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int
    page: int
    limit: int