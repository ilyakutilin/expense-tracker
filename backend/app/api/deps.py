from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependency import require_admin, require_user
from app.core.db import get_db_session
from app.schemas.auth import UserDep
from app.services import (
    AccountService,
    AuthService,
    CurrencyService,
    TagService,
    TransactionService,
    UserService,
)


def get_currency_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserDep = Depends(require_user),
) -> CurrencyService:
    """
    Currency service dependency.
    """
    return CurrencyService(db, user.id_)


def get_account_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserDep = Depends(require_user),
) -> AccountService:
    """
    Account service dependency.
    """
    return AccountService(db, user.id_)


def get_tag_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserDep = Depends(require_user),
) -> TagService:
    """
    Tag service dependency.
    """
    return TagService(db, user.id_)


def get_transaction_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserDep = Depends(require_user),
) -> TransactionService:
    """
    Transaction service dependency.
    """
    return TransactionService(db, user.id_)


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    Auth service dependency.
    """
    return AuthService(db)


def get_user_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserDep = Depends(require_admin),
) -> UserService:
    """
    User service dependency.
    """
    return UserService(db)
