from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud, models, schemas
from app.core import exceptions as exc


class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = crud.currency_crud

    async def create_currency(
        self, currency_create: schemas.CurrencyCreate
    ) -> schemas.CurrencyResponse:
        currency_exists = await self.crud.currency_exists(self.db, currency_create.code)
        if currency_exists:
            raise exc.ConflictError(
                message=f"Currency with code '{currency_create.code}' already exists",
                detail={"code": currency_create.code},
            )
        currency_data: dict[str, Any] = currency_create.model_dump()
        db_obj: models.CurrencyORM = await self.crud.create_currency(
            self.db, currency_data
        )
        return schemas.CurrencyResponse.model_validate(db_obj)

    async def get_all_currencies(self) -> list[schemas.CurrencyResponse]:
        currencies: list[models.CurrencyORM] = await self.crud.get_all_currencies(
            self.db
        )
        return [schemas.CurrencyResponse.model_validate(c) for c in currencies]
