from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
)

from app.core.settings import settings
from app.schemas import CurrencyResponse

MAX_PRECISION = settings.NUMERIC_PRECISION
MAX_SCALE = settings.NUMERIC_SCALE


class AccountType(str, Enum):
    ASSET = "asset"
    INCOME = "income"
    EXPENSE = "expense"


class AccountBase(BaseModel):
    parent_id: int | None
    currency_id: int | None
    balance: Decimal | None = Field(Decimal("0.00"))

    @field_validator("balance", mode="after")
    @classmethod
    def validate_balance_precision_and_scale(cls, v: Decimal):
        _, digits, exponent = v.as_tuple()

        total_digits = len(digits)
        if total_digits > MAX_PRECISION:
            raise ValueError(
                (
                    f"Numeric value has {total_digits} total digits, which exceeds "
                    f"the max precision of {MAX_PRECISION}."
                )
            )

        # Exponent is negative for a value with a fractional part.
        # e.g., Decimal('1.23').as_tuple() -> (0, (1, 2, 3), -2). Scale is |-2| = 2.
        if not isinstance(exponent, int):
            raise ValueError("Failed to validate the scale of the numeric value.")
        scale = -exponent
        if scale > MAX_SCALE:
            raise ValueError(
                (
                    f"Numeric value has {scale} decimal places, which exceeds "
                    f"the max scale of {MAX_SCALE}."
                )
            )

        return v


class AccountCreate(AccountBase):
    name: str = Field(..., min_length=1, max_length=100)
    type_: AccountType = Field(..., validation_alias="type")


class AccountUpdate(AccountBase):
    name: str | None = Field(None, min_length=1, max_length=100)
    type_: AccountType | None = Field(None, validation_alias="type")


class AccountResponseNested(BaseModel):
    id_: int = Field(serialization_alias="id")
    name: str
    type_: str = Field(serialization_alias="type")

    model_config = ConfigDict(from_attributes=True)


class AccountResponse(BaseModel):
    id_: int = Field(serialization_alias="id")
    name: str
    type_: str = Field(serialization_alias="type")
    parent: AccountResponseNested | None
    currency: CurrencyResponse | None
    balance: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_serializer(mode="wrap")
    def sort_keys(self, handler: SerializerFunctionWrapHandler) -> dict[str, int | str]:
        serialized = handler(self)
        key_order = [
            "id",
            "name",
            "type",
            "parent_id",
            "currency_id",
            "balance",
            "created_at",
            "updated_at",
        ]
        return {k: serialized[k] for k in key_order}
