from app.crud.base import CRUDBase
from app.models.transaction import TransactionORM


class CRUDTransaction(CRUDBase[TransactionORM]):
    pass


transaction_crud = CRUDTransaction(TransactionORM)
