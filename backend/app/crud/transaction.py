from app.crud.base import CRUDBase
from app.models import TransactionORM


class CRUDTransaction(CRUDBase[TransactionORM]):
    pass


transaction_crud = CRUDTransaction(TransactionORM)
