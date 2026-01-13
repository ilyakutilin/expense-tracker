import math
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud
from app.core import exceptions as exc
from app.filters.currency import CurrencyFilterParams
from app.models.currency import CurrencyORM
from app.schemas import currency as schemas
from app.schemas.pagination import PaginatedResponse


class CurrencyService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.crud: crud.CRUDCurrency = crud.currency_crud

    async def _get_currency_orm(
        self, currency_id: int, include_deleted: bool = False
    ) -> CurrencyORM:
        currency: CurrencyORM | None = await self.crud.get_by_id(
            self.db,
            obj_id=currency_id,
            user_id=self.user_id,
            include_deleted=include_deleted,
        )
        if not currency:
            raise exc.NotFoundError(
                message=f"Currency with id {currency_id} not found",
                detail={"id": currency_id, "user_id": self.user_id},
            )
        return currency

    async def _check_code_exists(self, code: str) -> None:
        currency: bool = await self.crud.exists(
            self.db, user_id=self.user_id, code=code
        )
        if currency:
            raise exc.ConflictError(
                message=f"Currency with code '{code}' already exists",
                detail={"code": code, "user_id": self.user_id},
            )

    async def create_currency(
        self, currency_create: schemas.CurrencyCreate
    ) -> schemas.CurrencyResponse:
        await self._check_code_exists(currency_create.code)
        currency_data: dict[str, Any] = currency_create.model_dump()
        currency_data["user_id"] = self.user_id
        currency_id: int = await self.crud.create(
            self.db, obj_data=currency_data, commit=True
        )
        currency_orm: CurrencyORM | None = await self.crud.get_by_id(
            self.db, obj_id=currency_id, user_id=self.user_id, include_deleted=False
        )
        if not currency_orm:
            raise exc.DatabaseError(
                message=("Created currency could not be fetched from the database"),
                detail={
                    "id": currency_id,
                    "code": currency_create.code,
                    "user_id": self.user_id,
                },
            )
        return schemas.CurrencyResponse.model_validate(currency_orm)

    async def update_currency(
        self, currency_id: int, currency_update: schemas.CurrencyUpdate
    ) -> schemas.CurrencyResponse:
        currency_orm: CurrencyORM = await self._get_currency_orm(currency_id)

        if currency_update.code:
            await self._check_code_exists(currency_update.code)

        currency_data: dict[str, Any] = currency_update.model_dump(exclude_unset=True)
        if not currency_data:
            raise exc.BadRequestError(
                message="No fields to update", detail={"id": currency_id}
            )

        updated_currency_id: int | None = await self.crud.update(
            db_session=self.db, orm_obj=currency_orm, data=currency_data
        )
        updated_currency_orm: CurrencyORM | None = None
        if updated_currency_id:
            updated_currency_orm: CurrencyORM | None = await self.crud.get_by_id(
                self.db, obj_id=updated_currency_id, user_id=self.user_id
            )
            if not updated_currency_orm:
                raise exc.DatabaseError(
                    message=("Updated currency could not be fetched from the database"),
                    detail={"id": currency_id, "user_id": self.user_id},
                )
        else:
            updated_currency_orm = currency_orm

        return schemas.CurrencyResponse.model_validate(updated_currency_orm)

    async def delete_currency(self, currency_id: int, perm: bool = False) -> None:
        currency: CurrencyORM = await self._get_currency_orm(currency_id, perm)

        await self.crud.delete(self.db, obj_orm=currency, perm=perm)

    async def get_currency(self, currency_id: int) -> schemas.CurrencyResponse:
        currency_orm: CurrencyORM = await self._get_currency_orm(currency_id)
        return schemas.CurrencyResponse.model_validate(currency_orm)

    async def get_all_currencies(
        self,
        filter_params: CurrencyFilterParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[schemas.CurrencyResponse]:
        conditions = filter_params.manager.build_conditions(filter_params)

        currency_orms, total_count = await self.crud.get_all(
            db_session=self.db,
            filter_conditions=conditions,
            user_id=self.user_id,
            include_deleted=include_deleted,
            unique=False,
        )
        currencies = [schemas.CurrencyResponse.model_validate(c) for c in currency_orms]

        return PaginatedResponse(
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=currencies,
        )
