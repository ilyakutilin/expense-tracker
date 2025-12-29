import datetime as dt
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from app.core.settings import settings
from app.schemas import StrippedStr
from app.schemas.account import AccountResponseBaseWithCurrency
from app.schemas.tag import TagResponseBase
from app.utils.fmt import format_monetary_decimal

MAX_PRECISION = settings.NUMERIC_PRECISION
MAX_SCALE = settings.NUMERIC_SCALE


class _Unset:
    pass


UNSET = _Unset()


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    EXCHANGE = "exchange"
    INITIAL = "initial"
    CORRECTION = "correction"
    REFUND = "refund"


def _validate_tag_ids(tag_ids: list[int]) -> list[int]:
    # Ensure uniqueness
    tag_ids = list(dict.fromkeys(tag_ids))
    if len(tag_ids) > 100:
        raise ValueError("Cannot assign more than 100 tags to a transaction")

    return tag_ids


class TransactionLineCreate(BaseModel):
    id_: PositiveInt | None = Field(None, validation_alias="id")
    transaction_id: PositiveInt | None = None
    account_id: PositiveInt
    amount: Decimal

    @field_validator("amount", mode="after")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Amount cannot be zero")

        exponent = v.as_tuple().exponent

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

        max_value = 10 ** (MAX_PRECISION - MAX_SCALE)
        if v >= max_value:
            raise ValueError(
                (
                    f"Amount value shall be between {-max_value} and {max_value} "
                    "(not inclusive)"
                )
            )

        return v


class TransactionCreate(BaseModel):
    type_: TransactionType = Field(..., validation_alias="type")
    date: dt.date = dt.date.today()
    comment: StrippedStr | None = Field(None, min_length=1, max_length=1000)
    is_template: bool = False
    lines: list[TransactionLineCreate] = Field(..., exclude=True)
    tag_ids: list[PositiveInt] = Field([], exclude=True)

    @field_validator("lines", mode="after")
    @classmethod
    def validate_lines(
        cls, v: list[TransactionLineCreate]
    ) -> list[TransactionLineCreate]:
        v.sort(key=lambda x: x.amount)

        if not (v[0].amount < 0 and v[1].amount > 0):
            raise ValueError(
                "Amounts in transaction lines shall be with opposite signs"
            )

        if v[0].account_id == v[1].account_id:
            raise ValueError(
                "Cannot credit the amount to the same account it is debited from"
            )

        return v

    @field_validator("tag_ids", mode="after")
    @classmethod
    def validate_tag_ids(cls, v: list[int]) -> list[int]:
        return _validate_tag_ids(v)

    @model_validator(mode="after")
    def validate_line_count(self) -> Self:
        single_line_types = (TransactionType.INITIAL, TransactionType.CORRECTION)

        if self.type_ in single_line_types and len(self.lines) != 1:
            raise ValueError(
                (
                    "There should be exacly one transaction line for a transaction "
                    f"of type '{self.type_.value}'; got {len(self.lines)}"
                )
            )

        if self.type_ not in single_line_types and len(self.lines) != 2:
            raise ValueError(
                (
                    "There should be exacly two transaction lines for a transaction "
                    f"of type '{self.type_.value}'; got {len(self.lines)}"
                )
            )

        return self


class TransactionLineUpdate(BaseModel):
    id_: PositiveInt = Field(..., validation_alias="id")
    account_id: PositiveInt | None = None
    amount: Decimal | None = None


class TransactionUpdate(BaseModel):
    type_: TransactionType | None = Field(None, validation_alias="type")
    date: dt.date | None = None
    comment: StrippedStr | None | _Unset = Field(UNSET, max_length=1000)
    is_template: bool | None = None
    lines: list[TransactionLineUpdate] | None = Field(None, exclude=True)
    tag_ids: list[int] | None = Field(None, exclude=True)

    @field_validator("tag_ids", mode="after")
    @classmethod
    def validate_tag_ids(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None

        return _validate_tag_ids(v)

    @model_validator(mode="after")
    def check_at_least_one_field_set(self) -> Self:
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("At least one field must be set")
        return self

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TransactionLineResponse(BaseModel):
    id_: int = Field(serialization_alias="id")
    account: AccountResponseBaseWithCurrency
    amount: Decimal
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: format_monetary_decimal},
    )


class TransactionResponse(BaseModel):
    id_: int = Field(..., serialization_alias="id")
    type_: TransactionType = Field(..., serialization_alias="type")
    lines: list[TransactionLineResponse] = Field(..., exclude=True)
    from_: TransactionLineResponse | None = Field(None, serialization_alias="from")
    to: TransactionLineResponse | None = None
    date: dt.date
    comment: str | None
    is_template: bool
    tags: list[TagResponseBase]
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: format_monetary_decimal},
    )

    @model_validator(mode="after")
    def split_lines(self) -> "TransactionResponse":
        lines = self.lines

        if len(lines) != 2:
            raise ValueError(f"Expected exactly 2 transaction lines, got {len(lines)}")

        if any(line.amount == 0 for line in lines):
            raise ValueError("Transaction line amounts cannot be zero")

        negative_lines = [line for line in lines if line.amount < 0]
        positive_lines = [line for line in lines if line.amount > 0]

        if len(negative_lines) != 1 or len(positive_lines) != 1:
            raise ValueError(
                "Expected exactly one negative and one positive amount, "
                f"got {len(negative_lines)} negative and {len(positive_lines)} positive"
            )

        self.from_ = negative_lines[0]
        self.to = positive_lines[0]

        return self
