from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import CurrencyORM


class CRUDCurrency(CRUDBase):
    async def get_currency_by_code(
        self,
        db_session: AsyncSession,
        code: str,
    ) -> CurrencyORM | None:
        query = select(CurrencyORM).where(
            and_(CurrencyORM.code == code, CurrencyORM.is_active)
        )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()


currency_crud = CRUDCurrency(CurrencyORM)
