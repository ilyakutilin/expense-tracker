import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import Sequence

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from app.core.i18n import _, n_, translate
from app.core.settings import settings
from app.schemas import StrippedStr
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
    CORRECTION = "correction"
    REFUND = "refund"


def _validate_lines(
    type_: TransactionType, lines: Sequence["TransactionLineBase"]
) -> None:
    for line in lines:
        if line.account_id is None or line.amount is None:
            raise ValueError(
                translate(
                    _(
                        "Account ID and amount cannot be None "
                        "for the purpose of lines validation"
                    )
                )
            )

    if type_ == TransactionType.CORRECTION and len(lines) != 1:
        translated_msg = translate(
            n_(
                "There should be exacly one transaction line for a transaction of type "
                "'{type}'; got {len_lines}",
                "There should be exacly one transaction line for a transaction of type "
                "'{type}'; got {len_lines}",
            )
            .set_n(len(lines))
            .set_kwargs(type=type_.value, len_lines=len(lines))
        )
        raise ValueError(translated_msg)

    if type_ != TransactionType.CORRECTION:
        if len(lines) != 2:
            translated_msg = translate(
                n_(
                    "There should be exacly two transaction lines for a transaction "
                    "of type '{type}'; got {len_lines}",
                    "There should be exacly two transaction lines for a transaction "
                    "of type '{type}'; got {len_lines}",
                )
                .set_n(len(lines))
                .set_kwargs(type=type_.value, len_lines=len(lines))
            )
            raise ValueError(translated_msg)

        if (lines[0].amount == 0) != (lines[1].amount == 0):
            raise ValueError(
                translate(
                    _(
                        "Amounts in transaction lines shall either both be zero "
                        "or shall both be the non-zero values with opposite signs"
                    )
                )
            )

        if any([line.amount != 0 for line in lines]):
            lines.sort(key=lambda x: x.amount)  # type: ignore

        if not (lines[0].amount < 0 and lines[1].amount > 0):  # type: ignore
            raise ValueError(
                translate(
                    _("Amounts in transaction lines shall be with opposite signs")
                )
            )

        if lines[0].account_id == lines[1].account_id:
            raise ValueError(
                translate(
                    _("Cannot credit the amount to the same account it is debited from")
                )
            )


class TransactionLineBase(BaseModel):
    id_: PositiveInt | None
    transaction_id: PositiveInt | None
    account_id: PositiveInt | None
    amount: Decimal | None

    @field_validator("amount", mode="after")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return None

        exponent = v.as_tuple().exponent

        # Exponent is negative for a value with a fractional part.
        # e.g., Decimal('1.23').as_tuple() -> (0, (1, 2, 3), -2). Scale is |-2| = 2.
        if not isinstance(exponent, int):
            raise ValueError(
                translate(_("Failed to validate the scale of the numeric value."))
            )
        scale = -exponent
        if scale > MAX_SCALE:
            translated_msg = translate(
                n_(
                    "Numeric value has {scale} decimal place, which exceeds "
                    "the max scale of {max_scale}.",
                    "Numeric value has {scale} decimal places, which exceeds "
                    "the max scale of {max_scale}.",
                )
                .set_n(scale)
                .set_kwargs(scale=scale, max_scale=MAX_SCALE)
            )
            raise ValueError(translated_msg)

        max_value = 10 ** (MAX_PRECISION - MAX_SCALE)
        if v >= max_value:
            translated_msg = translate(
                _(
                    "Amount value shall be between {max_value_negative} "
                    "and {max_value_positive} (not inclusive)"
                ).set_kwargs(
                    max_value_negative=-max_value, max_value_positive=max_value
                )
            )
            raise ValueError(translated_msg)

        return v


class TransactionLineCreate(TransactionLineBase):
    id_: PositiveInt | None = Field(None, validation_alias="id")
    transaction_id: PositiveInt | None = None
    account_id: PositiveInt
    amount: Decimal


class TransactionLineUpdate(TransactionLineBase):
    id_: PositiveInt = Field(..., validation_alias="id", exclude=True)
    transaction_id: PositiveInt | None = Field(None, exclude=True)
    account_id: PositiveInt | None = None
    amount: Decimal | None = None


class TransactionLineFull(TransactionLineBase):
    id_: PositiveInt = Field(..., validation_alias="id")
    transaction_id: PositiveInt
    account_id: PositiveInt
    amount: Decimal


class TransactionValidatorMixin:
    @field_validator("tag_ids", mode="after")
    @classmethod
    def validate_tag_ids(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None

        v = list(dict.fromkeys(v))
        if len(v) > 100:
            raise ValueError(
                translate(_("Cannot assign more than 100 tags to a transaction"))
            )

        return v


class TransactionCreate(TransactionValidatorMixin, BaseModel):
    type_: TransactionType = Field(..., validation_alias="type")
    date: dt.date = dt.date.today()
    comment: StrippedStr | None = Field(None, min_length=1, max_length=1000)
    is_template: bool = False
    lines: list[TransactionLineCreate] = Field(..., exclude=True)
    tag_ids: list[PositiveInt] = Field([], exclude=True)

    @model_validator(mode="after")
    def validate_lines(self) -> Self:
        _validate_lines(self.type_, self.lines)
        return self


class TransactionUpdate(TransactionValidatorMixin, BaseModel):
    type_: TransactionType | None = Field(None, validation_alias="type")
    date: dt.date | None = None
    comment: StrippedStr | None = Field(None, max_length=1000)
    is_template: bool | None = None
    lines: list[TransactionLineUpdate] | None = Field(None, exclude=True)
    full_lines: list[TransactionLineFull] | None = Field(None, exclude=True)
    tag_ids: list[int] | None = Field(None, exclude=True)

    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode="after")
    def check_at_least_one_field_set(self) -> Self:
        if not self.model_dump(exclude_unset=True):
            raise ValueError(translate(_("At least one field must be set")))
        return self

    @model_validator(mode="after")
    def validate_full_lines(self) -> Self:
        if self.full_lines is None:
            return self

        if self.type_ is None:
            raise ValueError(
                translate(
                    _("Transaction type shall be set when validating the full lines")
                )
            )

        _validate_lines(self.type_, self.full_lines)
        return self


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
    lines: list[TransactionLineResponse] | None = Field(None, exclude=True)
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
        if self.lines is None and (self.from_ is None or self.to is None):
            raise ValueError(
                translate(
                    _("Either the 'lines', or 'to' and 'from' fields shall be set")
                )
            )

        if self.lines is None and self.from_ is not None and self.to is not None:
            return self

        lines = self.lines
        assert lines is not None

        if len(lines) != 2:
            translated_msg = translate(
                n_(
                    "Expected exactly 2 transaction lines, got {len_lines}",
                    "Expected exactly 2 transaction lines, got {len_lines}",
                )
                .set_n(len(lines))
                .set_kwargs(len_lines=len(lines))
            )
            raise ValueError(translated_msg)

        if any(line.amount == 0 for line in lines):
            raise ValueError(translate(_("Transaction line amounts cannot be zero")))

        negative_lines = [line for line in lines if line.amount < 0]
        positive_lines = [line for line in lines if line.amount > 0]

        if len(negative_lines) != 1 or len(positive_lines) != 1:
            translated_msg = translate(
                _(
                    "Expected exactly one negative and one positive amount, got "
                    "{len_negative_lines} negative and {len_positive_lines} positive"
                ).set_kwargs(
                    len_negative_lines=len(negative_lines),
                    len_positive_lines=len(positive_lines),
                )
            )
            raise ValueError(translated_msg)

        self.from_ = negative_lines[0]
        self.to = positive_lines[0]

        return self
