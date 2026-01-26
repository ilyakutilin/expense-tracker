import math
from enum import Enum
from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.core.cache import cached, invalidate_cache
from app.core.i18n import _
from app.filters.transaction import TransactionFilterParams
from app.models.transaction import TransactionLineORM, TransactionORM
from app.schemas.cache import CachePattern, Entity
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionLineFull,
    TransactionLineUpdate,
    TransactionResponse,
    TransactionType,
    TransactionUpdate,
)
from app.services import get_msg

DETAIL_PATTERN = CachePattern(
    entity=Entity.TRANSACTION,
    obj_id_key="transaction_id",
    is_user_owned=True,
)

LIST_PATTERN = CachePattern(
    entity=Entity.TRANSACTION,
    obj_id_key=None,
    is_user_owned=True,
)


class TransactionService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.crud: crud.CRUDTransaction = crud.transaction_crud
        self.line_crud: crud.CRUDTransactionLine = crud.transaction_line_crud
        self.account_crud: crud.CRUDAccount = crud.account_crud
        self.tag_crud: crud.CRUDTag = crud.tag_crud

    async def _check_referential_integrity(
        self, account_ids: list[int], tag_ids: list[int] | None
    ) -> None:
        detail: dict[str, int | list[int]] = {}

        if account_ids:
            existing_acc_ids: list[int] = await self.account_crud.exist_multiple(
                self.db, ids=account_ids, user_id=self.user_id
            )
            missing_acc_ids = [
                aid for aid in account_ids if aid not in existing_acc_ids
            ]
            if missing_acc_ids:
                detail["account_ids"] = missing_acc_ids

        if tag_ids:
            existing_tag_ids: list[int] = await self.tag_crud.exist_multiple(
                self.db, ids=tag_ids, user_id=self.user_id
            )
            missing_acc_ids = [tid for tid in tag_ids if tid not in existing_tag_ids]
            if missing_acc_ids:
                detail["tag_ids"] = missing_acc_ids

        if detail:
            detail["user_id"] = self.user_id
            raise exc.ReferentialIntergrityError(
                message=_(
                    "Referential integrity violation: no record(s) "
                    "by the specified id(s)"
                ),
                detail=detail,
            )

    async def _get_transaction_orm_by_id(
        self, transaction_id: int, include_deleted: bool = False
    ) -> TransactionORM:
        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db,
            obj_id=transaction_id,
            user_id=self.user_id,
            include_deleted=include_deleted,
        )
        if not transaction_orm:
            raise exc.NotFoundError(
                message=get_msg(
                    _("Transaction with id {transaction_id} not found"),
                    transaction_id=transaction_id,
                ),
                detail={
                    "id": transaction_id,
                    "user_id": self.user_id,
                },
            )
        return transaction_orm

    @cached(pattern=DETAIL_PATTERN, response_model=TransactionResponse)
    async def get_transaction_by_id(
        self, *, transaction_id: int, include_deleted: bool = False
    ) -> TransactionResponse:
        transaction_orm: TransactionORM = await self._get_transaction_orm_by_id(
            transaction_id, include_deleted
        )
        return TransactionResponse.model_validate(transaction_orm)

    @cached(pattern=LIST_PATTERN, response_model=PaginatedResponse[TransactionResponse])
    async def get_all_transactions(
        self,
        *,
        filter_params: TransactionFilterParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[TransactionResponse]:
        conditions = filter_params.manager.build_conditions(filter_params)

        transaction_orms, total_count = await self.crud.get_all(
            db_session=self.db,
            filter_conditions=conditions,
            user_id=self.user_id,
            include_deleted=include_deleted,
            unique=True,
        )
        transactions = [TransactionResponse.model_validate(t) for t in transaction_orms]

        if total_count is None:
            raise exc.CodeError("Total count of transactions cannot be None")

        return PaginatedResponse[TransactionResponse](
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=transactions,
        )

    @invalidate_cache(LIST_PATTERN)
    async def create_transaction(self, *, tc: TransactionCreate) -> TransactionResponse:
        from_, to = tc.lines
        await self._check_referential_integrity(
            [from_.account_id, to.account_id], tc.tag_ids
        )
        transaction_data: dict[str, Any] = tc.model_dump()
        transaction_data["user_id"] = self.user_id
        transaction_id: int = await self.crud.create(
            self.db, obj_data=transaction_data, commit=False
        )

        for line in tc.lines:
            line.transaction_id = transaction_id
        lines_data: list[dict[str, Any]] = [line.model_dump() for line in tc.lines]
        await self.line_crud.create_multiple(self.db, data=lines_data, commit=False)

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
                    message=_("Failed to add some tags to the transaction"),
                    detail={
                        "failed_ids": list(failed).sort(),
                    },
                )

        await self.crud.commit(self.db)

        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db, obj_id=transaction_id, user_id=self.user_id, include_deleted=False
        )
        if not transaction_orm:
            raise exc.DatabaseError(
                message=(
                    _("Created transaction could not be fetched from the database")
                ),
                detail={"id": transaction_id, "user_id": self.user_id},
            )

        return TransactionResponse.model_validate(transaction_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def update_transaction(
        self, *, transaction_id: int, tu: TransactionUpdate
    ) -> TransactionResponse:
        """Update the transaction by the given ID based on the provided data.

        A 'transaction' here is undersatood as a whole, being comprised of the
        transaction 'proper' (it's ID, type, date, comment, etc.), transaction lines
        (having the corresponding account IDs and the amounts), and tags associations
        (a many-to-many relationship via a secondary table). And the API endpoint
        instructs to update all of that in one go. So the user can update any of the
        'proper' fields, any of the lines (providing their IDs in the request body),
        or the list of tags associated with this transaction. And on the DB side it
        will all look like separate operations because those are operations on three
        separate tables.

        Args:
            transaction_id (int): Transaction ID from the API request URL.
            tu (TransactionUpdate): Update data.

        Raises:
            ReferentialIntergrityError: Raised if account IDs of the transaction lines
                or the tag IDs do not exist in the DB, or if the IDs of the
                transaction lines in the update data don't match the IDs of the
                original transaction lines.
            RequestValidationError: Raised if the transaction lines fail validation
                so that the user is shown 422 Unprocessable Entity instead of 500
                that is normally served for Pydantic validation errors.

        Returns:
            TransactionResponse: A response object based on the updated ORM object
                from the DB.
        """
        # Check if the accounts IDs and tag IDs actually exist in DB.
        # Raise if they don't.
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

        # Make sure that the line IDs intended for update match the existing line IDs.
        # Raise if they don't.
        if tu.lines:
            existing_line_ids = set([line.id_ for line in t_orm.lines])
            updated_line_ids = {line.id_ for line in tu.lines}
            if not updated_line_ids.issubset(existing_line_ids):
                raise exc.ReferentialIntergrityError(
                    message=_("Transaction line IDs do not match the transaction"),
                    detail={
                        "transaction_id": t_orm.id_,
                        "existing_line_ids": list(existing_line_ids).sort(),
                        "updated_line_ids": list(updated_line_ids).sort(),
                    },
                )

        # Construct TransactionLineFull schemas in order to validate the complete
        # set of data for the lines. The values will be the updated values
        # if set in the update schema, or old existing values otherwise
        tu_lines = tu.lines if tu.lines is not None else []
        tu_line_ids = {line.id_ for line in tu_lines}
        full_lines: list[TransactionLineFull] = []
        for ex_line in t_orm.lines:
            line_data: dict[str, Any] = {
                "id": ex_line.id_,
                "transaction_id": transaction_id,
            }
            if ex_line.id_ in tu_line_ids:
                new_line: TransactionLineUpdate = [
                    line for line in tu_lines if line.id_ == ex_line.id_
                ][0]
                line_data["account_id"] = new_line.account_id or ex_line.account_id
                line_data["amount"] = (
                    new_line.amount if new_line.amount is not None else ex_line.amount
                )

            else:
                line_data["account_id"] = ex_line.account_id
                line_data["amount"] = ex_line.amount

            full_lines.append(TransactionLineFull.model_validate(line_data))

        # Validate the transaction lines based on full set of data (old + new)
        try:
            # Type shall be set in order for the schema model_validator to work
            if not tu.type_:
                tu.type_ = TransactionType(t_orm.type_)
            # This should trigger validation due to validate_assignment=True in schema
            tu.full_lines = full_lines
        except ValidationError as e:
            # In case validations fails, it needs to be communicated to the user
            # as a true validation error, not 500. Hence give it to FastAPI to handle.
            raise RequestValidationError(errors=e.errors())

        class UpdateStatus(int, Enum):
            """Transaction update status.

            This indicates whether anything has been actually updated in the DB or not.
            The idea is that if there any changes to the transaction itself,
            its transaction lines, or the array of tags it's associated with,
            the transaction record should be marked as updated in the DB with the
            corresponding change of the updated_at, even if no 'proper' fields of the
            transaction record were actually updated. Therefore this serves as a
            'tracker' so that if there are changes in the lines, or in the tags
            associations, we can manually 'mark' the main Transaction object
            as updated.

            Values:
                UNDEFINED: We don't know if anything was updated or not.
                UPDATED: The main Transaction object has already been marked as updated
                    because one of its 'proper' fields was changed, so the manual
                    action is not required.
                REQUIRED: The main Transaction object has not been marked as updated,
                    but there are changes in the transaction lines and / or the tags.
                    So the transaction needs to be marked as updated manually.
            """

            UNDEFINED = 0
            UPDATED = 1
            REQUIRED = 2

        update_status = UpdateStatus.UNDEFINED
        # Update the main transaction object in the DB
        update_data: dict[str, Any] = tu.model_dump(exclude_unset=True, by_alias=True)
        updated_transaction_id: int | None = await self.crud.update(
            self.db, orm_obj=t_orm, data=update_data, commit=False
        )
        if updated_transaction_id is not None:
            update_status = UpdateStatus.UPDATED

        # Update the lines in the DB
        for tu_line in tu_lines:
            data = tu_line.model_dump(exclude_unset=True)
            line_orm: TransactionLineORM = [
                line for line in t_orm.lines if line.id_ == tu_line.id_
            ][0]
            updated_line_id: int | None = await self.line_crud.update(
                self.db, orm_obj=line_orm, data=data, commit=False
            )
            if updated_line_id is not None and update_status != UpdateStatus.UPDATED:
                update_status = UpdateStatus.REQUIRED

        # Update the tags in the DB
        if tu.tag_ids and set(tu.tag_ids).issubset({tag.id_ for tag in t_orm.tags}):
            await self.crud.update_transaction_tags(
                db_session=self.db,
                transaction_id=transaction_id,
                existing_tag_ids=[tag.id_ for tag in t_orm.tags],
                new_tag_ids=tu.tag_ids,
                commit=False,
            )
            if update_status != UpdateStatus.UPDATED:
                update_status = UpdateStatus.REQUIRED

        if update_status == UpdateStatus.REQUIRED:
            await self.crud.mark_updated(self.db, orm_obj=t_orm, commit=False)

        await self.crud.commit(self.db)

        transaction_orm: TransactionORM | None = await self.crud.get_by_id(
            self.db, obj_id=transaction_id, user_id=self.user_id, include_deleted=False
        )

        if not transaction_orm:
            raise exc.CodeError(
                (
                    f"Could not fetch the updated transaction from the DB after update."
                    f" Transaction ID: {transaction_id}, User ID: {self.user_id}"
                )
            )

        return TransactionResponse.model_validate(transaction_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def delete_transaction(
        self, *, transaction_id: int, perm: bool = False
    ) -> None:
        transaction_orm: TransactionORM = await self._get_transaction_orm_by_id(
            transaction_id, perm
        )

        # Transaction lines and the transaction_tags records will be cascaded if perm
        await self.crud.delete(self.db, obj_orm=transaction_orm, perm=perm)

        if not perm:
            # TODO: Better introduce delete_multiple in CRUD
            for line in transaction_orm.lines:
                await self.line_crud.delete(self.db, obj_orm=line, perm=False)
