from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import TagORM


class CRUDTag(CRUDBase[TagORM]):
    async def exists_by_name(
        self, db_session: AsyncSession, tag_name: str, include_deleted: bool = False
    ) -> bool:
        stmt = select(self.model.id_).where(self.model.name == tag_name)
        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
        result = await db_session.scalar(stmt)
        return result is not None


tag_crud = CRUDTag(TagORM)
