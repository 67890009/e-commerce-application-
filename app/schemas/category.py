from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True

class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool

class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int
    page: int
    limit: int