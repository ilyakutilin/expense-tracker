from sqlalchemy import and_, delete, func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.filters.base import FilterConditions
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

    async def get_all_transactions(
        self,
        db_session: AsyncSession,
        include_deleted: bool = False,
        filter_conditions: FilterConditions | None = None,
    ) -> tuple[list[TransactionORM], int | None]:
        stmt = select(self.model)
        count_stmt = select(func.count(self.model.id_))

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
            count_stmt = count_stmt.where(self.model.is_active)

        total_count: int | None = None
        if filter_conditions:
            if filter_conditions.has_filters():
                for condition in filter_conditions.where_clauses:
                    stmt = stmt.where(condition)
                    count_stmt = count_stmt.where(condition)

            total_count_result = await db_session.execute(count_stmt)
            total_count = total_count_result.scalar()

            stmt = stmt.options(*self._get_options())

            if filter_conditions.has_ordering():
                for order_clause in filter_conditions.order_by_clauses:
                    stmt = stmt.order_by(order_clause)

            if filter_conditions.has_pagination():
                offset, limit = filter_conditions.offset_limit
                stmt = stmt.offset(offset).limit(limit)

        stmt = stmt.options(*self._get_options())

        result = await db_session.execute(stmt)
        transaction_orms = list(result.scalars().unique().all())

        return transaction_orms, total_count

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

    async def update_transaction_tags(
        self,
        db_session: AsyncSession,
        transaction_id: int,
        existing_tag_ids: list[int],
        new_tag_ids: list[int],
        commit: bool = True,
    ) -> None:
        if set(existing_tag_ids) == set(new_tag_ids):
            return

        to_delete = [tag_id for tag_id in existing_tag_ids if tag_id not in new_tag_ids]
        to_insert = [tag_id for tag_id in new_tag_ids if tag_id not in existing_tag_ids]

        try:
            if to_delete:
                delete_stmt = delete(transaction_tag).where(
                    and_(
                        transaction_tag.c.transaction_id == transaction_id,
                        transaction_tag.c.tag_id.in_(to_delete),
                    )
                )
                await db_session.execute(delete_stmt)

            if to_insert:
                insert_stmt = insert(transaction_tag).values(
                    [
                        {"transaction_id": transaction_id, "tag_id": tag_id}
                        for tag_id in to_insert
                    ]
                )
                await db_session.execute(insert_stmt)

            if commit:
                await db_session.commit()

            return

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
