from sqlalchemy.orm import selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.models.account import AccountORM
from app.models.currency import CurrencyORM
from app.models.tag import TagORM
from app.models.transaction import TransactionLineORM, TransactionORM


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


transaction_crud = CRUDTransaction(TransactionORM)
