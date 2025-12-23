from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.models.account import AccountORM
from app.models.currency import CurrencyORM


class CRUDAccount(CRUDBase[AccountORM]):
    @classmethod
    def _get_options(cls) -> tuple[_AbstractLoad, ...]:
        return (
            joinedload(AccountORM.parent).load_only(
                AccountORM.id_, AccountORM.name, AccountORM.type_
            ),
            joinedload(AccountORM.currency).load_only(
                CurrencyORM.id_, CurrencyORM.code, CurrencyORM.symbol
            ),
        )

    async def name_exists(
        self,
        db_session: AsyncSession,
        name: str,
    ) -> bool:
        stmt = select(self.model.id_).where(
            and_(self.model.name == name, self.model.is_active)
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_name(
        self, db_session: AsyncSession, name: str, include_deleted: bool = False
    ) -> AccountORM | None:
        stmt = select(self.model).where(self.model.name == name)
        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
        stmt = stmt.options(*self._get_options())
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()


account_crud = CRUDAccount(AccountORM)
