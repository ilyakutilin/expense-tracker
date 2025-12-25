from typing import Any

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
        self.line_crud: crud.CRUDTransactionLine = crud.transaction_line_crud
        self.account_crud: crud.CRUDAccount = crud.account_crud
        self.tag_crud: crud.CRUDTag = crud.tag_crud

    def _prevent_self_transfer(self, from_acc_id: int, to_acc_id: int) -> None:
        if from_acc_id == to_acc_id:
            raise exc.ReferentialIntergrityError(
                message="From account and to account must be different",
                detail={"from_acc_id": from_acc_id, "to_acc_id": to_acc_id},
            )

    async def _check_referential_integrity(
        self, account_ids: list[int], tag_ids: list[int] | None
    ) -> None:
        detail: dict[str, int | list[int]] = {}

        if account_ids:
            existing_acc_ids: list[int] = await self.account_crud.exist_multiple(
                self.db, account_ids
            )
            missing_acc_ids = [
                aid for aid in account_ids if aid not in existing_acc_ids
            ]
            if missing_acc_ids:
                detail["account_ids"] = missing_acc_ids

        if tag_ids:
            existing_tag_ids: list[int] = await self.tag_crud.exist_multiple(
                self.db, tag_ids
            )
            missing_acc_ids = [tid for tid in tag_ids if tid not in existing_tag_ids]
            if missing_acc_ids:
                detail["tag_ids"] = missing_acc_ids

        if detail:
            raise exc.ReferentialIntergrityError(
                message=(
                    "Referential integrity violation: no record(s) "
                    "by the specified id(s)"
                ),
                detail=detail,
            )

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

    async def create_transaction(self, tc: TransactionCreate) -> TransactionResponse:
        from_, to = tc.lines
        await self._check_referential_integrity(
            [from_.account_id, to.account_id], tc.tag_ids
        )
        transaction_data: dict[str, Any] = tc.model_dump()
        pre_orm: TransactionORM = await self.crud.create(
            self.db, transaction_data, refresh=True, commit=False
        )

        for line in tc.lines:
            line.transaction_id = pre_orm.id_
            line_data: dict[str, Any] = line.model_dump()
            await self.line_crud.create(self.db, line_data, refresh=False, commit=False)

        if tc.tag_ids:
            inserted_tag_ids = await self.crud.insert_transaction_tags(
                db_session=self.db,
                transaction_id=pre_orm.id_,
                tag_ids=tc.tag_ids,
                commit=False,
            )
            failed = set(tc.tag_ids) - set(inserted_tag_ids)
            if failed:
                raise exc.DatabaseError(
                    message="Failed to add some tags to the transaction",
                    detail={
                        "failed_ids": list(failed).sort(),
                    },
                )

        await self.crud.commit(self.db)

        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db, obj_id=pre_orm.id_, include_deleted=False
        )
        if not transaction_orm:
            raise exc.DatabaseError(
                message=("Created transaction could not be fetched from the database"),
                detail={"id": pre_orm.id_},
            )

        return TransactionResponse.model_validate(transaction_orm)

    async def update_transaction(
        self, transaction_id: int, transaction_update: TransactionUpdate
    ) -> TransactionResponse:  # type: ignore
        pass

    async def delete_transaction(self, transaction_id: int, perm: bool = False) -> None:
        pass
