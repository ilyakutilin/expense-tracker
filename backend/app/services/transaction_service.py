import math
from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.filters.base import FilterManager
from app.filters.transaction import TransactionFilterParams, transaction_filter_manager
from app.models.transaction import TransactionLineORM, TransactionORM
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import (
    UNSET,
    TransactionCreate,
    TransactionLineUpdate,
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

    async def _get_transaction_orm_by_id(
        self, transaction_id: int, include_deleted: bool = False
    ) -> TransactionORM:
        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db, transaction_id, include_deleted
        )
        if not transaction_orm:
            raise exc.NotFoundError(
                message=f"Transaction with id {transaction_id} not found",
                detail={"id": transaction_id},
            )
        return transaction_orm

    async def get_transaction_by_id(
        self, transaction_id: int, include_deleted: bool = False
    ) -> TransactionResponse:
        transaction_orm: TransactionORM = await self._get_transaction_orm_by_id(
            transaction_id, include_deleted
        )
        return TransactionResponse.model_validate(transaction_orm)

    async def get_all_transactions(
        self,
        filter_params: TransactionFilterParams,
        filter_manager: FilterManager = transaction_filter_manager,
        include_deleted: bool = False,
    ) -> PaginatedResponse[TransactionResponse]:
        conditions = filter_manager.build_conditions(filter_params)

        transaction_orms, total_count = await self.crud.get_all_transactions(
            db_session=self.db,
            include_deleted=include_deleted,
            filter_conditions=conditions,
        )
        tranactions = [TransactionResponse.model_validate(t) for t in transaction_orms]

        if total_count is None:
            raise exc.CodeError("Total count of transactions cannot be None")

        return PaginatedResponse(
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=tranactions,
        )

    async def create_transaction(self, tc: TransactionCreate) -> TransactionResponse:
        from_, to = tc.lines
        await self._check_referential_integrity(
            [from_.account_id, to.account_id], tc.tag_ids
        )
        transaction_data: dict[str, Any] = tc.model_dump()
        transaction_id: int = await self.crud.create(
            self.db, transaction_data, commit=False
        )

        for line in tc.lines:
            line.transaction_id = transaction_id
        lines_data: list[dict[str, Any]] = [line.model_dump() for line in tc.lines]
        await self.line_crud.create_multiple(self.db, lines_data, commit=False)

        if tc.tag_ids:
            inserted_tag_ids = await self.crud.insert_transaction_tags(
                db_session=self.db,
                transaction_id=transaction_id,
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
            self.db, obj_id=transaction_id, include_deleted=False
        )
        if not transaction_orm:
            raise exc.DatabaseError(
                message=("Created transaction could not be fetched from the database"),
                detail={"id": transaction_id},
            )

        return TransactionResponse.model_validate(transaction_orm)

    async def update_transaction(
        self, transaction_id: int, tu: TransactionUpdate
    ) -> TransactionResponse:
        # Check if the accounts IDs and tag IDs actually exist in DB
        account_ids = (
            []
            if tu.lines is None
            else [line.account_id for line in tu.lines if line.account_id is not None]
        )
        tag_ids = [] if tu.tag_ids is None else tu.tag_ids
        await self._check_referential_integrity(account_ids, tag_ids)

        # Get the current state of the transaction and place the ORM object in session
        t_orm: TransactionORM = await self._get_transaction_orm_by_id(
            transaction_id, include_deleted=False
        )

        # Make sure that the line IDs intended for update match the existing line IDs
        if tu.lines:
            existing_line_ids = set([line.id_ for line in t_orm.lines])
            updated_line_ids = {line.id_ for line in tu.lines}
            if not updated_line_ids.issubset(existing_line_ids):
                raise exc.ReferentialIntergrityError(
                    message="Transaction line IDs do not match the transaction",
                    detail={
                        "transaction_id": t_orm.id_,
                        "existing_line_ids": list(existing_line_ids).sort(),
                        "updated_line_ids": list(updated_line_ids).sort(),
                    },
                )

        # Construct a full TransactionCreate schema in order to validate the complete
        # set of data. The values will be the updated values if set in the update schema
        # or old existing values otherwise
        tu_lines = tu.lines if tu.lines is not None else []
        tu_line_ids = {line.id_ for line in tu_lines}
        lines: list[dict[str, Any]] = []
        for ex_line in t_orm.lines:
            if ex_line.id_ in tu_line_ids:
                new_line: TransactionLineUpdate = [
                    line for line in tu_lines if line.id_ == ex_line.id_
                ][0]
            else:
                # Create a dummy update schema instance to avoid AttributeErrors later
                new_line = TransactionLineUpdate.model_validate({"id": ex_line.id_})
            # Create a TransactionLineCreate instance to run the validations
            line_create_data = {
                "id": new_line.id_,
                "account_id": new_line.account_id or ex_line.account.id_,
                "amount": new_line.amount
                if new_line.amount is not None
                else ex_line.amount,
            }
            lines.append(line_create_data)

        # Validate the whole set of data (updated incorporated into existing)
        transaction_create_data = {
            "type": tu.type_ or t_orm.type_,
            "date": tu.date or t_orm.date,
            "comment": tu.comment if tu.comment is not UNSET else t_orm.comment,
            "is_template": tu.is_template
            if tu.is_template is not None
            else t_orm.is_template,
            "lines": lines,
            "tag_ids": tag_ids,
        }
        try:
            validated_create_model = TransactionCreate.model_validate(
                transaction_create_data
            )
        except ValidationError as e:
            raise RequestValidationError(errors=e.errors())

        # Update the main transaction object in the DB
        update_data: dict[str, Any] = validated_create_model.model_dump()
        updated_transaction_id: int = await self.crud.update(
            self.db, t_orm, update_data, commit=False
        )

        # Update the lines in the DB
        for vl in validated_create_model.lines:
            if vl.id_ not in tu_line_ids:
                continue
            data = vl.model_dump(exclude_unset=True)
            line_orm: TransactionLineORM = [
                line for line in t_orm.lines if line.id_ == vl.id_
            ][0]
            await self.line_crud.update(self.db, line_orm, data, commit=False)

        # Update the tags in the DB
        if validated_create_model.tag_ids:
            await self.crud.update_transaction_tags(
                db_session=self.db,
                transaction_id=transaction_id,
                existing_tag_ids=[tag.id_ for tag in t_orm.tags],
                new_tag_ids=validated_create_model.tag_ids,
                commit=False,
            )

        await self.crud.commit(self.db)

        return await self.get_transaction_by_id(updated_transaction_id)

    async def delete_transaction(self, transaction_id: int, perm: bool = False) -> None:
        pass
