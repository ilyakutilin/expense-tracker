from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models import AccountORM, CurrencyORM


class CRUDAccount(CRUDBase[AccountORM]):
    async def get_by_id(
        self, db_session: AsyncSession, obj_id: int, include_deleted: bool = False
    ) -> AccountORM | None:
        stmt = select(self.model).where(self.model.id_ == obj_id)
        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
        stmt = stmt.options(
            joinedload(AccountORM.parent).load_only(
                AccountORM.id_, AccountORM.name, AccountORM.type_
            ),
            joinedload(AccountORM.currency).load_only(
                CurrencyORM.id_, CurrencyORM.code, CurrencyORM.symbol
            ),
        )
        result = await db_session.execute(stmt)
        return result.unique().scalar_one_or_none()

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
