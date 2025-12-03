from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app import crud, schemas
from app.core import exceptions as exc
from app.models.currency import CurrencyORM


class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = crud.currency_crud

    async def create_currency(
        self, currency_create: schemas.CurrencyCreate
    ) -> schemas.CurrencyDB:
        currency_exists = await self.crud.currency_exists(self.db, currency_create.code)
        if currency_exists:
            raise exc.ConflictError(
                message=f"Currency with code '{currency_create.code}' already exists",
                detail={"code": currency_create.code},
            )
        currency_data: dict[str, Any] = currency_create.model_dump()
        db_obj: CurrencyORM = await self.crud.create_currency(self.db, currency_data)
        return schemas.CurrencyDB.model_validate(db_obj, by_alias=True)
