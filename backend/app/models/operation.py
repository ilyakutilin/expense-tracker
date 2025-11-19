import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseORM
from app.models.base import BaseModelORM

if TYPE_CHECKING:
    from backend.app.models.account import AccountORM
    from backend.app.models.currency import CurrencyORM
    from backend.app.models.tag import TagORM


class OperationType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    EXCHANGE = "exchange"
    INITIAL = "initial"
    CORRECTION = "correction"
    REFUND = "refund"

    @classmethod
    def get_values(cls) -> set[str]:
        return {t.value for t in cls}


operation_tag = Table(
    "operation_tag",
    BaseORM.metadata,
    Column("operation_id", ForeignKey("operation.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class OperationORM(BaseModelORM):
    __tablename__ = "operation"

    type_: Mapped[str] = mapped_column(
        "type",
        String(50),
        CheckConstraint(
            f"type in {', '.join(OperationType.get_values())}",
            name="chk_operation_type",
        ),
        index=True,
    )
    from_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    to_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    amount: Mapped[int]
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"), index=True
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=16, scale=6, decimal_return_scale=6, asdecimal=True),
        default=Decimal("1.0"),
    )
    commission: Mapped[int] = mapped_column(default=0)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    comment: Mapped[str] = mapped_column(Text, default="", index=True)
    is_template: Mapped[bool] = mapped_column(default=False, index=True)

    from_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[from_acc_id],
        back_populates="operations_from",
    )

    to_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[to_acc_id],
        back_populates="operations_to",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        secondary=operation_tag,
        back_populates="operations",
        lazy="selectin",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="operations",
    )
