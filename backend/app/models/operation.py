import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    tag_id: Mapped[int | None] = mapped_column(
        ForeignKey("tag.id", ondelete="SET NULL"), index=True
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
    date: Mapped[dt.date]
    comment: Mapped[str] = mapped_column(Text, default="")
    is_template: Mapped[bool] = mapped_column(default=False)

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

    tag: Mapped["TagORM | None"] = relationship(
        "TagORM",
        back_populates="operations",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="operations",
    )
