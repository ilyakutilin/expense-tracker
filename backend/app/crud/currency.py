from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CurrencyORM
from app.schemas import CurrencyCreate


class CRUDCurrency:
    async def create_currency(
        self, currency_schema: CurrencyCreate, db_session: AsyncSession
    ):
        try:
            currency_data = currency_schema.model_dump()
            db_currency = CurrencyORM(**currency_data)

            db_session.add(db_currency)
            await db_session.commit()
            await db_session.refresh(db_currency)

            return db_currency

        except SQLAlchemyError as e:
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}",
            )
        except Exception as e:
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error occurred: {str(e)}",
            )


currency_crud = CRUDCurrency()
