import math
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.models.tag import TagFilter, TagORM
from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagCreateUpdate, TagResponse


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDTag = crud.tag_crud

    async def _check_name_exists(
        self, name: str, include_deleted: bool = False
    ) -> None:
        exists: bool = await self.crud.exists(self.db, include_deleted, name=name)
        if exists:
            raise exc.ConflictError(
                message=f"Tag with name '{name}' already exists",
                detail={"name": name},
            )

    async def _get_tag_orm_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagORM:
        tag_orm: TagORM | None = await self.crud.get_by_id(
            self.db, tag_id, include_deleted
        )
        if not tag_orm:
            raise exc.NotFoundError(
                message=f"Tag with id {tag_id} not found",
                detail={"id": tag_id},
            )
        return tag_orm

    async def get_tag_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagResponse:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id, include_deleted)
        return TagResponse.model_validate(tag_orm)

    async def get_all_tags(
        self,
        include_deleted: bool = False,
        filter_: TagFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TagResponse]:
        tags_orm, total = await self.crud.get_all(
            db_session=self.db,
            include_deleted=include_deleted,
            filter_=filter_,
            page=page,
            page_size=page_size,
        )
        tags = [TagResponse.model_validate(t) for t in tags_orm]
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
            items=tags,
        )

    async def create_tag(self, tag_create: TagCreateUpdate) -> TagResponse:
        await self._check_name_exists(tag_create.name)
        tag_data: dict[str, Any] = tag_create.model_dump()
        tag_id: int = await self.crud.create(self.db, tag_data, commit=True)
        tag_orm: TagORM | None = await self.crud.get_by_id(
            self.db, tag_id, include_deleted=False
        )
        if not tag_orm:
            raise exc.DatabaseError(
                message=("Created tag could not be fetched from the database"),
                detail={"id": tag_id, "name": tag_create.name},
            )
        return TagResponse.model_validate(tag_orm)

    async def update_tag(self, tag_id: int, tag_update: TagCreateUpdate) -> TagResponse:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id)

        await self._check_name_exists(tag_update.name)

        tag_data: dict[str, Any] = tag_update.model_dump()

        updated_tag_id: int = await self.crud.update(
            db_session=self.db, orm_obj=tag_orm, data=tag_data
        )
        return await self.get_tag_by_id(updated_tag_id)

    async def delete_tag(self, tag_id: int, perm: bool = False) -> None:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id, perm)

        await self.crud.delete(self.db, tag_orm, perm)
