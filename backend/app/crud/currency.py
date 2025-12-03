from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CurrencyORM


class CRUDCurrency:
    async def currency_exists(
        self,
        db_session: AsyncSession,
        code: str,
    ) -> bool:
        query = select(CurrencyORM).where(CurrencyORM.code == code)
        result = await db_session.execute(query)
        return result.scalar_one_or_none() is not None

    async def create_currency(
        self,
        db_session: AsyncSession,
        currency_data: dict,
    ) -> CurrencyORM:
        try:
            db_currency = CurrencyORM(**currency_data)

            db_session.add(db_currency)
            await db_session.commit()
            await db_session.refresh(db_currency)

            return db_currency

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def get_all_currencies(self, db_session: AsyncSession) -> list[CurrencyORM]:
        query = select(CurrencyORM)
        result = await db_session.execute(query)
        return list(result.scalars().all())


currency_crud = CRUDCurrency()
