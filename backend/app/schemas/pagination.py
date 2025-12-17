from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

from app.models.base import BaseORM

ModelType = TypeVar("ModelType", bound="BaseORM")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[ModelType]):
    items: List[ModelType]
    total: int
    page: int
    page_size: int
    total_pages: int
