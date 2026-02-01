import math
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.core.cache import cached, invalidate_cache
from app.core.i18n import _
from app.filters.account import AccountFilterParams
from app.models.account import AccountORM
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.schemas.cache import CachePattern, Entity
from app.schemas.pagination import PaginatedResponse

DETAIL_PATTERN = CachePattern(
    entity=Entity.ACCOUNT,
    obj_id_key="account_id",
    is_user_owned=True,
)

LIST_PATTERN = CachePattern(
    entity=Entity.ACCOUNT,
    obj_id_key=None,
    is_user_owned=True,
)


class AccountService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.crud: crud.CRUDAccount = crud.account_crud
        self.currency_crud: crud.CRUDCurrency = crud.currency_crud

    async def _get_account_orm_by_id(
        self, account_id: int, include_deleted: bool = False
    ) -> AccountORM:
        account_orm: AccountORM | None = await self.crud.get_by_id(
            self.db,
            obj_id=account_id,
            user_id=self.user_id,
            include_deleted=include_deleted,
        )
        if not account_orm:
            raise exc.NotFoundError(
                translatable_message=_("Account with id {account_id} not found"),
                account_id=account_id,
                detail={
                    "id": account_id,
                    "user_id": self.user_id,
                },
            )
        return account_orm

    async def _check_name_exists(self, name: str) -> None:
        exists: bool = await self.crud.exists(
            self.db,
            user_id=self.user_id,
            name=name,
        )
        if exists:
            raise exc.ConflictError(
                translatable_message=_("Account with name '{name}' already exists"),
                name=name,
                detail={
                    "name": name,
                    "user_id": self.user_id,
                },
            )

    async def _check_referential_integrity(
        self, parent_id: int | None, currency_id: int | None
    ) -> None:
        msg_txt = ""
        detail: dict[str, Any] = {"user_id": self.user_id}
        if parent_id:
            parent_exists = await self.crud.exists(
                self.db, user_id=self.user_id, id_=parent_id
            )
            if not parent_exists:
                detail["parent_id"] = parent_id
                msg_txt = _("Parent account with ID {parent_id} does not exist.")

        if currency_id:
            currency_exists = await self.currency_crud.exists(self.db, id_=currency_id)
            if not currency_exists:
                detail["currency_id"] = currency_id
                msg_txt = (
                    _("Currency with ID {currency_id} does not exist.")
                    if not msg_txt
                    else _(
                        (
                            "Parent account with ID {parent_id} and currency with ID "
                            "{currency_id} do not exist."
                        )
                    )
                )

        if msg_txt:
            raise exc.ReferentialIntergrityError(
                translatable_message=msg_txt,
                detail=detail,
                parent_id=parent_id,
                currency_id=currency_id,
            )

    def _prevent_self_parenting(self, account_id: int, parent_id: int) -> None:
        if account_id == parent_id:
            raise exc.ReferentialIntergrityError(
                translatable_message=_("An account cannot be a sub-account of itself"),
                detail={"account_id": account_id, "parent_id": parent_id},
            )

    @cached(pattern=DETAIL_PATTERN, response_model=AccountResponse)
    async def get_account_by_id(
        self, *, account_id: int, include_deleted: bool = False
    ) -> AccountResponse:
        account_orm: AccountORM = await self._get_account_orm_by_id(
            account_id, include_deleted
        )
        balance: Decimal = await self.crud.get_one_balance(self.db, account_orm.id_)
        return AccountResponse(**account_orm.__dict__, balance=balance)

    @cached(pattern=LIST_PATTERN, response_model=PaginatedResponse[AccountResponse])
    async def get_all_accounts(
        self,
        *,
        filter_params: AccountFilterParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[AccountResponse]:
        conditions = filter_params.manager.build_conditions(filter_params)

        account_orms, total_count = await self.crud.get_all(
            db_session=self.db,
            filter_conditions=conditions,
            user_id=self.user_id,
            include_deleted=include_deleted,
            unique=True,
        )
        essential_account_ids = [
            acc.id_ for acc in account_orms if not acc.has_children
        ]

        balances = await self.crud.get_multiple_balances(
            self.db, account_ids=essential_account_ids
        )
        accounts_with_balances = [
            (account, balances.get(account.id_)) for account in account_orms
        ]
        accounts = [
            AccountResponse(**account.__dict__, balance=balance)
            for account, balance in accounts_with_balances
        ]

        if total_count is None:
            raise exc.CodeError("Total count of accounts cannot be None")

        return PaginatedResponse[AccountResponse](
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=accounts,
        )

    @invalidate_cache(LIST_PATTERN)
    async def create_account(self, *, account_create: AccountCreate) -> AccountResponse:
        await self._check_name_exists(account_create.name)
        await self._check_referential_integrity(
            account_create.parent_id, account_create.currency_id
        )
        account_data: dict[str, Any] = account_create.model_dump()
        account_data["user_id"] = self.user_id
        account_id: int = await self.crud.create(
            self.db, obj_data=account_data, commit=True
        )
        account_orm: AccountORM | None = await self.crud.get_by_id(
            self.db, obj_id=account_id, include_deleted=False
        )
        if not account_orm:
            raise exc.DatabaseError(
                message="Created account could not be fetched from the database",
                detail={
                    "id": account_id,
                    "name": account_create.name,
                    "user_id": self.user_id,
                },
            )
        return AccountResponse.model_validate(account_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def update_account(
        self, *, account_id: int, account_update: AccountUpdate
    ) -> AccountResponse:
        account_orm: AccountORM = await self._get_account_orm_by_id(account_id)

        if account_update.name:
            await self._check_name_exists(account_update.name)
        await self._check_referential_integrity(
            account_update.parent_id, account_update.currency_id
        )

        if account_update.parent_id:
            self._prevent_self_parenting(account_id, account_update.parent_id)

        account_data: dict[str, Any] = account_update.model_dump(exclude_unset=True)
        if not account_data:
            raise exc.BadRequestError(
                translatable_message=_("No fields to update"), detail={"id": account_id}
            )

        updated_account_id: int | None = await self.crud.update(
            db_session=self.db, orm_obj=account_orm, data=account_data
        )
        updated_account_orm: AccountORM | None = None
        if updated_account_id:
            updated_account_orm: AccountORM | None = await self.crud.get_by_id(
                self.db, obj_id=updated_account_id
            )
            if not updated_account_orm:
                raise exc.DatabaseError(
                    message="Updated account could not be fetched from the database",
                    detail={"id": account_id, "user_id": self.user_id},
                )
        else:
            updated_account_orm = account_orm
        return AccountResponse.model_validate(updated_account_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def delete_account(self, *, account_id: int, perm: bool = False) -> None:
        account: AccountORM = await self._get_account_orm_by_id(account_id, perm)

        await self.crud.delete(self.db, obj_orm=account, perm=perm)
