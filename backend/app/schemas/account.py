from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from app.core.settings import settings
from app.schemas import StrippedStr
from app.schemas.currency import CurrencyResponse
from app.utils.fmt import format_monetary_decimal

MAX_PRECISION = settings.NUMERIC_PRECISION
MAX_SCALE = settings.NUMERIC_SCALE


class AccountType(str, Enum):
    ASSET = "asset"
    INCOME = "income"
    EXPENSE = "expense"


class AccountBase(BaseModel):
    parent_id: PositiveInt | None
    currency_id: PositiveInt | None


class AccountCreate(AccountBase):
    name: StrippedStr = Field(..., min_length=1, max_length=100)
    type_: AccountType = Field(..., validation_alias="type")


class AccountUpdate(AccountBase):
    name: StrippedStr | None = Field(None, min_length=1, max_length=100)
    type_: AccountType | None = Field(None, validation_alias="type")


class AccountResponseBase(BaseModel):
    id_: PositiveInt = Field(serialization_alias="id")
    name: str
    type_: str = Field(serialization_alias="type")

    model_config = ConfigDict(from_attributes=True)


class AccountResponseBaseWithCurrency(AccountResponseBase):
    currency: CurrencyResponse | None


class AccountResponse(AccountResponseBaseWithCurrency):
    parent: AccountResponseBase | None
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: format_monetary_decimal},
    )

    @model_serializer(mode="wrap")
    def sort_keys(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        serialized = handler(self)
        id_field_name, type_field_name = "id", "type"
        if any([k.endswith("_") for k in serialized]):
            id_field_name, type_field_name = "id_", "type_"
        key_order = [
            id_field_name,
            "name",
            type_field_name,
            "parent",
            "currency",
            "balance",
            "created_at",
            "updated_at",
        ]
        return {k: serialized[k] for k in key_order}
