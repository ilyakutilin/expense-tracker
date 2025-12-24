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

from app.core.settings import settings
from app.schemas.account import AccountResponseBaseWithCurrency
from app.schemas.tag import TagResponseBase
from app.utils.fmt import format_monetary_decimal

MAX_PRECISION = settings.NUMERIC_PRECISION
MAX_SCALE = settings.NUMERIC_SCALE


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    EXCHANGE = "exchange"
    INITIAL = "initial"
    CORRECTION = "correction"
    REFUND = "refund"


class TransactionValidators(BaseModel):
    @field_validator("from_amount", "to_amount", mode="after", check_fields=False)
    @classmethod
    def validate_decimal_precision_and_scale(cls, v: Decimal) -> Decimal:
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

    @field_validator("lines", mode="after")
    @classmethod
    def sort_lines_by_amount(
        cls, v: list["TransactionLineCreate"]
    ) -> list["TransactionLineCreate"]:
        return sorted(v, key=lambda x: x.amount)


class TransactionLineCreate(TransactionValidators):
    account_id: PositiveInt
    amount: Decimal

    @field_validator("amount", mode="after")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Amount cannot be zero")

        max_val = 10 ** (MAX_PRECISION - MAX_SCALE)
        if v <= Decimal(-max_val) or v >= Decimal(max_val):
            raise ValueError(
                f"Amount limit is {max_val}, not inclusive, regardless of the sign"
            )

        return v


class TransactionCreate(TransactionValidators):
    type_: TransactionType = Field(..., validation_alias="type")
    date: dt.date = dt.date.today()
    comment: str | None = Field(None, max_length=1000)
    is_template: bool = False
    lines: list[TransactionLineCreate]
    tag_ids: list[PositiveInt] = []

    @field_validator("lines", mode="after")
    @classmethod
    def validate_lines(
        cls, v: list[TransactionLineCreate]
    ) -> list[TransactionLineCreate]:
        if len(v) != 2:
            raise ValueError(
                "There should be exactly two transaction lines in a transaction"
            )

        # By this moment the lines are already sorted by amount
        if not (v[0].amount < 0 and v[1].amount > 0):
            raise ValueError(
                "Amounts in transaction lines shall be with opposite signs"
            )

        if v[0].account_id == v[1].account_id:
            raise ValueError("Accounts in the transaction lines shall be different")

        return v

    @field_validator("tag_ids", mode="after")
    @classmethod
    def validate_tag_ids(cls, v: list[int]) -> list[int]:
        v = list(dict.fromkeys(v))
        if len(v) > 100:
            raise ValueError("Cannot assign more than 100 tags to a transaction")

        return v


class TransactionLineUpdate(TransactionValidators):
    account_id: int | None = Field(None, ge=1)
    amount: Decimal | None = None


class TransactionUpdate(TransactionValidators):
    type_: TransactionType | None = Field(None, validation_alias="type")
    date: dt.date | None = None
    comment: str | None = Field(None, max_length=1000)
    is_template: bool | None = None
    lines: list[TransactionLineUpdate] | None = None
    tag_ids: list[int] | None = None


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
