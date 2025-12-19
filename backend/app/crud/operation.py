from app.crud.base import CRUDBase
from app.models import OperationORM


class CRUDOperation(CRUDBase[OperationORM]):
    pass


operation_crud = CRUDOperation(OperationORM)
