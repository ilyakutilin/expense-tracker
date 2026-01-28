from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.models.account import AccountORM
from app.models.currency import CurrencyORM
from app.models.transaction import TransactionLineORM, TransactionORM


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

    async def get_one_balance(
        self, db_session: AsyncSession, account_id: int
    ) -> Decimal:
        stmt = (
            select(
                func.sum(TransactionLineORM.amount),
            )
            .join(TransactionORM)
            .where(
                TransactionLineORM.account_id == account_id,
                TransactionLineORM.is_deleted == False,  # noqa: E712
                TransactionORM.is_deleted == False,  # noqa: E712
                TransactionORM.is_template == False,  # noqa: E712
            )
        )

        result = await db_session.execute(stmt)
        result = result.scalar_one_or_none()
        if result is None:
            return Decimal(0)
        return result

    async def get_multiple_balances(
        self, db_session: AsyncSession, account_ids: list[int]
    ) -> dict[int, Decimal]:
        stmt = (
            select(
                TransactionLineORM.account_id,
                func.sum(TransactionLineORM.amount).label("balance"),
            )
            .join(TransactionORM)
            .where(
                TransactionLineORM.account_id.in_(account_ids),
                TransactionLineORM.is_deleted == False,  # noqa: E712
                TransactionORM.is_deleted == False,  # noqa: E712
                TransactionORM.is_template == False,  # noqa: E712
            )
            .group_by(TransactionLineORM.account_id)
        )

        result = await db_session.execute(stmt)
        return {row.account_id: row.balance for row in result}


account_crud = CRUDAccount(AccountORM)
