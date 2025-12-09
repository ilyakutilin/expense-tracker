from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import AccountORM


class CRUDAccount(CRUDBase[AccountORM]):
    async def get_account_by_name(
        self,
        db_session: AsyncSession,
        name: str,
    ) -> AccountORM | None:
        query = select(AccountORM).where(
            and_(AccountORM.name == name, AccountORM.is_active)
        )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()


account_crud = CRUDAccount(AccountORM)
