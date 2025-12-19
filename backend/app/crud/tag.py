from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import TagORM


class CRUDTag(CRUDBase[TagORM]):
    async def get_tag_by_name(
        self,
        db_session: AsyncSession,
        name: str,
    ) -> TagORM | None:
        query = select(TagORM).where(and_(TagORM.name == name, TagORM.is_active))
        result = await db_session.execute(query)
        return result.scalar_one_or_none()


tag_crud = CRUDTag(TagORM)
