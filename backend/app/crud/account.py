from sqlalchemy.orm import joinedload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.crud.base import CRUDBase
from app.models.account import AccountORM
from app.models.currency import CurrencyORM


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


account_crud = CRUDAccount(AccountORM)
