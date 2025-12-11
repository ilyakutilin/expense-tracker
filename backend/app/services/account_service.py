from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud, models
from app.core import exceptions as exc
from app.schemas import account as schemas


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDAccount = crud.account_crud
        self.currency_crud: crud.CRUDCurrency = crud.currency_crud

    async def get_account_by_id(
        self, account_id: int, include_deleted: bool = False
    ) -> schemas.AccountResponse:
        account_orm: models.AccountORM | None = await self.crud.get_by_id(
            self.db, account_id, include_deleted
        )
        if not account_orm:
            raise exc.NotFoundError(
                message=f"Account with id {account_id} not found",
                detail={"id": account_id},
            )
        return schemas.AccountResponse.model_validate(account_orm)

    async def _check_name_exists(self, name: str) -> None:
        account_orm: models.AccountORM | None = await self.crud.get_account_by_name(
            self.db, name
        )
        if account_orm:
            raise exc.ConflictError(
                message=f"Account with name '{name}' already exists",
                detail={"name": name},
            )

    async def _check_referential_integrity(
        self, parent_id: int | None, currency_id: int | None
    ) -> None:
        msg_txt = ""
        detail: dict[str, int] = {}
        if parent_id:
            parent_exists = await self.crud.exists(self.db, parent_id)
            if not parent_exists:
                detail["parent_id"] = parent_id
                msg_txt = f"Parent account with ID {parent_id} does not exist."

        if currency_id:
            currency_exists = await self.currency_crud.exists(self.db, currency_id)
            if not currency_exists:
                detail["currency_id"] = currency_id
                msg_txt = (
                    f"Currency with ID {currency_id} does not exist."
                    if not msg_txt
                    else (
                        f"Parent account with ID {parent_id} and currency with ID "
                        f"{currency_id} do not exist."
                    )
                )

        if msg_txt:
            raise exc.RelatedResourceNotFoundError(message=msg_txt, detail=detail)

    async def create_account(
        self, account_create: schemas.AccountCreate
    ) -> schemas.AccountResponse:
        await self._check_name_exists(account_create.name)
        await self._check_referential_integrity(
            account_create.parent_id, account_create.currency_id
        )
        currency_data: dict[str, Any] = account_create.model_dump()
        account_orm: models.AccountORM = await self.crud.create(self.db, currency_data)
        return schemas.AccountResponse.model_validate(account_orm)

    async def delete_account(self, account_id: int, perm: bool = False) -> None:
        pass

    async def get_all_accounts(self) -> list[schemas.AccountResponse]:
        pass
