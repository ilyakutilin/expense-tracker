from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud, models
from app.core import exceptions as exc
from app.schemas import currency as schemas


class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDCurrency = crud.currency_crud

    async def _get_currency_by_id(
        self, currency_id: int, include_deleted: bool = False
    ) -> models.CurrencyORM:
        currency: models.CurrencyORM | None = await self.crud.get_by_id(
            self.db, currency_id, include_deleted
        )
        if not currency:
            raise exc.NotFoundError(
                message=f"Currency with id {currency_id} not found",
                detail={"id": currency_id},
            )
        return currency

    async def _check_code_exists(self, code: str) -> None:
        currency: models.CurrencyORM | None = await self.crud.get_currency_by_code(
            self.db, code
        )
        if currency:
            raise exc.ConflictError(
                message=f"Currency with code '{code}' already exists",
                detail={"code": code},
            )

    async def create_currency(
        self, currency_create: schemas.CurrencyCreate
    ) -> schemas.CurrencyResponse:
        await self._check_code_exists(currency_create.code)
        currency_data: dict[str, Any] = currency_create.model_dump()
        db_obj: models.CurrencyORM = await self.crud.create(self.db, currency_data)
        return schemas.CurrencyResponse.model_validate(db_obj)

    async def update_currency(
        self, currency_id: int, currency_update: schemas.CurrencyUpdate
    ) -> schemas.CurrencyResponse:
        currency: models.CurrencyORM = await self._get_currency_by_id(currency_id)

        if currency_update.code:
            await self._check_code_exists(currency_update.code)

        currency_data: dict[str, Any] = currency_update.model_dump(exclude_unset=True)
        if not currency_data:
            raise exc.BadRequestError(
                message="No fields to update", detail={"id": currency_id}
            )

        updated_currency: models.CurrencyORM = await self.crud.update(
            db_session=self.db, obj_orm=currency, obj_data=currency_data
        )

        return schemas.CurrencyResponse.model_validate(updated_currency)

    async def delete_currency(self, currency_id: int, perm: bool = False) -> None:
        currency: models.CurrencyORM = await self._get_currency_by_id(currency_id, perm)

        await self.crud.delete(self.db, currency, perm)

    async def get_all_currencies(self) -> list[schemas.CurrencyResponse]:
        currencies: list[models.CurrencyORM] = await self.crud.get_all(self.db)
        return [schemas.CurrencyResponse.model_validate(c) for c in currencies]
