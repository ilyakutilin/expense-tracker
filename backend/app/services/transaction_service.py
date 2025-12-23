from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.models.transaction import TransactionORM
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import (
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
        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db, transaction_id, include_deleted
        )
        if not transaction_orm:
            raise exc.NotFoundError(
                message=f"Transaction with id {transaction_id} not found",
                detail={"id": transaction_id},
            )
        return TransactionResponse.model_validate(transaction_orm)

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
