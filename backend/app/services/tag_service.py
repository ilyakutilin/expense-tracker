from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.models.base import BaseFilter
from app.schemas.tag import TagCreateUpdate, TagResponse


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDTag = crud.tag_crud

    async def get_tag_by_id(
        self, tag_id: int, include_deleted: bool = False
    ) -> TagResponse:
        return TagResponse(
            id_=0, name="", created_at=datetime.now(), updated_at=datetime.now()
        )

    async def get_all_tags(
        self,
        include_deleted: bool = False,
        filter_: BaseFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[TagResponse]:
        return []

    async def create_tag(self, tag_create: TagCreateUpdate) -> TagResponse:
        return TagResponse(
            id_=0, name="", created_at=datetime.now(), updated_at=datetime.now()
        )

    async def update_tag(self, tag_id: int, tag_update: TagCreateUpdate) -> TagResponse:
        return TagResponse(
            id_=0, name="", created_at=datetime.now(), updated_at=datetime.now()
        )

    async def delete_tag(self, tag_id: int, perm: bool = False) -> None:
        pass
