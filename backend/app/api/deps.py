from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.services import AccountService, CurrencyService, OperationService, TagService


def get_currency_service(db: AsyncSession = Depends(get_db_session)) -> CurrencyService:
    """
    Currency service dependency.
    """
    return CurrencyService(db)


def get_account_service(db: AsyncSession = Depends(get_db_session)) -> AccountService:
    """
    Account service dependency.
    """
    return AccountService(db)


def get_tag_service(db: AsyncSession = Depends(get_db_session)) -> TagService:
    """
    Tag service dependency.
    """
    return TagService(db)


def get_operation_service(
    db: AsyncSession = Depends(get_db_session),
) -> OperationService:
    """
    Operation service dependency.
    """
    return OperationService(db)
