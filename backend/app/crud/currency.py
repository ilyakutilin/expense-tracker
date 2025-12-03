from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CurrencyORM
from app.schemas import CurrencyDB


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
    ) -> CurrencyDB:
        try:
            db_currency = CurrencyORM(**currency_data)

            db_session.add(db_currency)
            await db_session.commit()
            await db_session.refresh(db_currency)

            return db_currency

        except SQLAlchemyError:
            await db_session.rollback()
            raise


currency_crud = CRUDCurrency()
