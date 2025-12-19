from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.schemas.operation import OperationCreate, OperationResponse, OperationUpdate
from app.schemas.pagination import PaginatedResponse


class OperationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDOperation = crud.operation_crud
        self.account_crud: crud.CRUDAccount = crud.account_crud
        self.currency_crud: crud.CRUDCurrency = crud.currency_crud

    async def get_operation_by_id(
        self, operation_id: int, include_deleted: bool = False
    ) -> OperationResponse:  # type: ignore
        pass

    async def get_all_operations(
        self,
        include_deleted: bool = False,
        filter_: Filter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[OperationResponse]:  # type: ignore
        pass

    async def create_operation(
        self, operation_create: OperationCreate
    ) -> OperationResponse:  # type: ignore
        pass

    async def update_operation(
        self, operation_id: int, operation_update: OperationUpdate
    ) -> OperationResponse:  # type: ignore
        pass

    async def delete_operation(self, operation_id: int, perm: bool = False) -> None:
        pass
