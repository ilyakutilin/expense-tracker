from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependency import get_current_user_id
from app.core.db import get_db_session
from app.services import (
    AccountService,
    AuthService,
    CurrencyService,
    TagService,
    TransactionService,
)


def get_currency_service(
    db: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> CurrencyService:
    """
    Currency service dependency.
    """
    return CurrencyService(db, user_id)


def get_account_service(
    db: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> AccountService:
    """
    Account service dependency.
    """
    return AccountService(db, user_id)


def get_tag_service(
    db: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> TagService:
    """
    Tag service dependency.
    """
    return TagService(db, user_id)


def get_transaction_service(
    db: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> TransactionService:
    """
    Transaction service dependency.
    """
    return TransactionService(db, user_id)


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    Auth service dependency.
    """
    return AuthService(db)
