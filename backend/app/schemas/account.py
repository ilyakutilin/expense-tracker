from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from app.core.settings import settings
from app.schemas.currency import CurrencyResponse
from app.utils.fmt import format_monetary_decimal

MAX_PRECISION = settings.NUMERIC_PRECISION
MAX_SCALE = settings.NUMERIC_SCALE


class AccountType(str, Enum):
    ASSET = "asset"
    INCOME = "income"
    EXPENSE = "expense"


class AccountBase(BaseModel):
    parent_id: int | None = Field(None, ge=1)
    currency_id: int | None = Field(None, ge=1)


class AccountCreate(AccountBase):
    name: str = Field(..., min_length=1, max_length=100)
    type_: AccountType = Field(..., validation_alias="type")


class AccountUpdate(AccountBase):
    name: str | None = Field(None, min_length=1, max_length=100)
    type_: AccountType | None = Field(None, validation_alias="type")


class AccountResponseBase(BaseModel):
    id_: int = Field(serialization_alias="id")
    name: str
    type_: str = Field(serialization_alias="type")

    model_config = ConfigDict(from_attributes=True)


class AccountResponseBaseWithCurrency(AccountResponseBase):
    currency: CurrencyResponse | None


class AccountResponse(AccountResponseBaseWithCurrency):
    parent: AccountResponseBase | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: format_monetary_decimal},
    )

    @model_serializer(mode="wrap")
    def sort_keys(self, handler: SerializerFunctionWrapHandler) -> dict[str, int | str]:
        serialized = handler(self)
        key_order = [
            "id",
            "name",
            "type",
            "parent",
            "currency",
            "created_at",
            "updated_at",
        ]
        return {k: serialized[k] for k in key_order}
