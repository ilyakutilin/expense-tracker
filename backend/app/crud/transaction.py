from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.models.account import AccountORM
from app.models.currency import CurrencyORM
from app.models.tag import TagORM
from app.models.transaction import TransactionLineORM, TransactionORM, transaction_tag


class CRUDTransaction(CRUDBase[TransactionORM]):
    @classmethod
    def _get_options(cls) -> tuple[_AbstractLoad, ...]:
        return (
            selectinload(TransactionORM.lines)
            .load_only(
                TransactionLineORM.id_,
                TransactionLineORM.amount,
                TransactionLineORM.created_at,
                TransactionLineORM.updated_at,
            )
            .joinedload(TransactionLineORM.account)
            .load_only(AccountORM.id_, AccountORM.name, AccountORM.type_)
            .joinedload(AccountORM.currency)
            .load_only(CurrencyORM.id_, CurrencyORM.code, CurrencyORM.symbol),
            selectinload(TransactionORM.tags).load_only(TagORM.id_, TagORM.name),
        )

    async def insert_transaction_tags(
        self,
        db_session: AsyncSession,
        transaction_id: int,
        tag_ids: list[int],
        commit: bool = True,
    ) -> list[int]:
        stmt = (
            insert(transaction_tag)
            .values(
                [
                    {"transaction_id": transaction_id, "tag_id": tag_id}
                    for tag_id in tag_ids
                ]
            )
            .returning(transaction_tag.c.tag_id)
        )
        try:
            result = await db_session.execute(stmt)
            if commit:
                await db_session.commit()
            return list(result.scalars().all())

        except SQLAlchemyError:
            await db_session.rollback()
            raise


class CRUDTransactionLine(CRUDBase[TransactionLineORM]):
    @classmethod
    def _get_options(cls) -> tuple[_AbstractLoad, ...]:
        return (
            joinedload(TransactionLineORM.account)
            .load_only(AccountORM.id_, AccountORM.name, AccountORM.type_)
            .joinedload(AccountORM.currency)
            .load_only(CurrencyORM.id_, CurrencyORM.code, CurrencyORM.symbol),
        )


transaction_crud = CRUDTransaction(TransactionORM)
transaction_line_crud = CRUDTransactionLine(TransactionLineORM)
