from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CurrencyORM


class CRUDCurrency:
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

    async def get_currency_by_id(
        self, db_session: AsyncSession, currency_id: int
    ) -> CurrencyORM | None:
        query = select(CurrencyORM).where(
            and_(CurrencyORM.id_ == currency_id, CurrencyORM.is_active)
        )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()

    async def create_currency(
        self,
        db_session: AsyncSession,
        currency_data: dict[str, Any],
    ) -> CurrencyORM:
        try:
            currency_orm = CurrencyORM(**currency_data)

            db_session.add(currency_orm)
            await db_session.commit()
            await db_session.refresh(currency_orm)

            return currency_orm

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def update_currency(
        self,
        db_session: AsyncSession,
        currency_orm: CurrencyORM,
        currency_data: dict[str, Any],
    ) -> CurrencyORM:
        for field, value in currency_data.items():
            setattr(currency_orm, field, value)

        try:
            db_session.add(currency_orm)
            await db_session.commit()
            await db_session.refresh(currency_orm)

            return currency_orm

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def get_all_currencies(self, db_session: AsyncSession) -> list[CurrencyORM]:
        query = select(CurrencyORM).where(CurrencyORM.is_active)
        result = await db_session.execute(query)
        return list(result.scalars().all())


currency_crud = CRUDCurrency()
