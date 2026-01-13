import math
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.filters.tag import TagFilterParams
from app.models.tag import TagORM
from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagCreateUpdate, TagResponse


class TagService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.crud: crud.CRUDTag = crud.tag_crud

    async def _check_name_exists(
        self, name: str, include_deleted: bool = False
    ) -> None:
        exists: bool = await self.crud.exists(
            self.db,
            user_id=self.user_id,
            include_deleted=include_deleted,
            name=name,
        )
        if exists:
            raise exc.ConflictError(
                message=f"Tag with name '{name}' already exists",
                detail={
                    "name": name,
                    "user_id": self.user_id,
                },
            )

    async def _get_tag_orm_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagORM:
        tag_orm: TagORM | None = await self.crud.get_by_id(
            self.db,
            obj_id=tag_id,
            user_id=self.user_id,
            include_deleted=include_deleted,
        )
        if not tag_orm:
            raise exc.NotFoundError(
                message=f"Tag with id {tag_id} not found",
                detail={
                    "id": tag_id,
                    "user_id": self.user_id,
                },
            )
        return tag_orm

    async def get_tag_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagResponse:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id, include_deleted)
        return TagResponse.model_validate(tag_orm)

    async def get_all_tags(
        self,
        filter_params: TagFilterParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[TagResponse]:
        conditions = filter_params.manager.build_conditions(filter_params)

        tag_orms, total_count = await self.crud.get_all(
            db_session=self.db,
            filter_conditions=conditions,
            user_id=self.user_id,
            include_deleted=include_deleted,
            unique=True,
        )
        tags = [TagResponse.model_validate(t) for t in tag_orms]

        if total_count is None:
            raise exc.CodeError("Total count of tags cannot be None")

        return PaginatedResponse[TagResponse](
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=tags,
        )

    async def create_tag(self, tag_create: TagCreateUpdate) -> TagResponse:
        await self._check_name_exists(tag_create.name)
        tag_data: dict[str, Any] = tag_create.model_dump()
        tag_data["user_id"] = self.user_id
        tag_id: int = await self.crud.create(self.db, obj_data=tag_data, commit=True)
        tag_orm: TagORM | None = await self.crud.get_by_id(
            self.db, obj_id=tag_id, include_deleted=False
        )
        if not tag_orm:
            raise exc.DatabaseError(
                message=("Created tag could not be fetched from the database"),
                detail={
                    "id": tag_id,
                    "name": tag_create.name,
                    "user_id": self.user_id,
                },
            )
        return TagResponse.model_validate(tag_orm)

    async def update_tag(self, tag_id: int, tag_update: TagCreateUpdate) -> TagResponse:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id)

        await self._check_name_exists(tag_update.name)

        tag_data: dict[str, Any] = tag_update.model_dump()

        updated_tag_id: int | None = await self.crud.update(
            db_session=self.db, orm_obj=tag_orm, data=tag_data
        )
        updated_tag_orm: TagORM | None = None
        if updated_tag_id:
            updated_tag_orm: TagORM | None = await self.crud.get_by_id(
                self.db, obj_id=updated_tag_id, user_id=self.user_id
            )
            if not updated_tag_orm:
                raise exc.DatabaseError(
                    message=("Updated account could not be fetched from the database"),
                    detail={
                        "id": tag_id,
                        "user_id": self.user_id,
                    },
                )
        else:
            updated_tag_orm = tag_orm
        return TagResponse.model_validate(updated_tag_orm)

    async def delete_tag(self, tag_id: int, perm: bool = False) -> None:
        tag_orm: TagORM = await self._get_tag_orm_by_id(tag_id, perm)

        await self.crud.delete(self.db, obj_orm=tag_orm, perm=perm)
