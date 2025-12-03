from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.services.currency_service import CurrencyService


def get_currency_service(db: AsyncSession = Depends(get_db_session)) -> CurrencyService:
    """
    Currency service dependency.
    """
    return CurrencyService(db)
