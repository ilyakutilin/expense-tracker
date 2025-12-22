from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.schemas.pagination import PaginatedResponse
from backend.app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDTransaction = crud.transaction_crud
        self.account_crud: crud.CRUDAccount = crud.account_crud
        self.currency_crud: crud.CRUDCurrency = crud.currency_crud

    async def get_transaction_by_id(
        self, transaction_id: int, include_deleted: bool = False
    ) -> TransactionResponse:  # type: ignore
        pass

    async def get_all_transactions(
        self,
        include_deleted: bool = False,
        filter_: Filter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TransactionResponse]:  # type: ignore
        pass

    async def create_transaction(
        self, transaction_create: TransactionCreate
    ) -> TransactionResponse:  # type: ignore
        pass

    async def update_transaction(
        self, transaction_id: int, transaction_update: TransactionUpdate
    ) -> TransactionResponse:  # type: ignore
        pass

    async def delete_transaction(self, transaction_id: int, perm: bool = False) -> None:
        pass
