from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.models.base import BaseFilter
from app.models.tag import TagORM
from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagCreateUpdate, TagResponse


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDTag = crud.tag_crud

    async def _check_name_exists(
        self, name: str, include_deleted: bool = False
    ) -> None:
        existing_id: int | None = await self.crud.exists_by_name(
            self.db, name, include_deleted
        )
        if existing_id:
            raise exc.ConflictError(
                message=f"Tag with name '{name}' already exists",
                detail={"id": existing_id, "name": name},
            )

    async def get_tag_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagResponse:
        return TagResponse(
            id_=0,
            name="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            operations_count=0,
        )

    async def get_all_tags(
        self,
        include_deleted: bool = False,
        filter_: BaseFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TagResponse]:
        return PaginatedResponse(
            total=0,
            page=0,
            page_size=0,
            total_pages=0,
            items=[],
        )

    async def create_tag(self, tag_create: TagCreateUpdate) -> TagResponse:
        await self._check_name_exists(tag_create.name)
        tag_data: dict[str, Any] = tag_create.model_dump()
        tag_orm: TagORM = await self.crud.create(self.db, tag_data)
        return TagResponse.model_validate(tag_orm)

    async def update_tag(self, tag_id: int, tag_update: TagCreateUpdate) -> TagResponse:
        return TagResponse(
            id_=0,
            name="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            operations_count=0,
        )

    async def delete_tag(self, tag_id: int, perm: bool = False) -> None:
        pass
