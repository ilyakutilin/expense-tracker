from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud, models, schemas
from app.core import exceptions as exc


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDAccount = crud.account_crud

    async def _get_account_by_id(
        self, account_id: int, include_deleted: bool = False
    ) -> models.AccountORM:
        account_orm: models.AccountORM | None = await self.crud.get_by_id(
            self.db, account_id, include_deleted
        )
        if not account_orm:
            raise exc.NotFoundError(
                message=f"Account with id {account_id} not found",
                detail={"id": account_id},
            )
        return account_orm

    async def _check_name_exists(self, name: str) -> None:
        account_orm: models.AccountORM | None = await self.crud.get_account_by_name(
            self.db, name
        )
        if account_orm:
            raise exc.ConflictError(
                message=f"Account with name '{name}' already exists",
                detail={"name": name},
            )

    async def create_account(
        self, account_create: schemas.AccountCreate
    ) -> schemas.AccountResponse:
        pass

    async def delete_account(self, account_id: int, perm: bool = False) -> None:
        pass

    async def get_all_accounts(self) -> list[schemas.AccountResponse]:
        pass
