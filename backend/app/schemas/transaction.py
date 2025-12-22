import datetime as dt
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.account import AccountResponseBaseWithCurrency
from app.schemas.tag import TagResponseBase
from app.utils.fmt import format_monetary_decimal


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    EXCHANGE = "exchange"
    INITIAL = "initial"
    CORRECTION = "correction"
    REFUND = "refund"


class TransactionValidators(BaseModel):
    pass


class TransactionCreate(TransactionValidators):
    type_: TransactionType = Field(..., validation_alias="type")
    from_acc_id: int = Field(..., ge=1)
    to_acc_id: int = Field(..., ge=1)
    from_amount: Decimal
    to_amount: Decimal | None = None
    date: dt.date = dt.date.today()
    comment: str | None = None
    is_template: bool = False
    tag_ids: list[int] | None = None

    @model_validator(mode="after")
    def set_to_amount_default(self):
        if self.to_amount is None:
            self.to_amount = self.from_amount
        return self


class TransactionUpdate(TransactionValidators):
    type_: TransactionType | None = Field(None, validation_alias="type")
    from_acc_id: int | None = Field(None, ge=1)
    to_acc_id: int | None = Field(None, ge=1)
    from_amount: Decimal | None = None
    to_amount: Decimal | None
    date: dt.date | None = None
    comment: str | None = None
    is_template: bool | None = None
    tag_ids: list[int] | None = None

    @model_validator(mode="after")
    def set_to_amount_default(self):
        if self.from_amount is not None and self.to_amount is None:
            self.to_amount = self.from_amount
        return self


class TransactionResponse(BaseModel):
    id_: int = Field(serialization_alias="id")
    type_: TransactionType = Field(serialization_alias="type")
    from_acc: AccountResponseBaseWithCurrency
    to_acc: AccountResponseBaseWithCurrency
    from_amount: Decimal
    to_amount: Decimal
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
