from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseORM
from app.models.mixins import CreatedUpdatedMixin

if TYPE_CHECKING:
    from app.models.currency import CurrencyORM
    from app.models.operation import OperationORM


class AccountORM(BaseORM, CreatedUpdatedMixin):
    name: Mapped[str] = mapped_column(Text, unique=True, index=True)
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), index=True
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"), index=True
    )
    balance: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=23, scale=8, decimal_return_scale=8, asdecimal=True),
        default=Decimal("0.0"),
    )

    parent: Mapped["AccountORM | None"] = relationship(
        "AccountORM",
        remote_side="AccountORM.id_",
        back_populates="children",
        foreign_keys=[parent_id],
    )

    children: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="accounts",
    )

    operations_from: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        foreign_keys="[OperationORM.from_acc_id]",
        back_populates="from_acc",
    )

    operations_to: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        foreign_keys="[OperationORM.to_acc_id]",
        back_populates="to_acc",
    )

    # Hybrid relationship that combines both from and to operations
    operations: Mapped[list["OperationORM"]] = relationship(
        primaryjoin="or_(AccountORM.id_==OperationORM.from_acc_id, AccountORM.id_==OperationORM.to_acc_id)",
        viewonly=True,
        lazy="select",
        overlaps="from_acc,to_acc",  # Important to avoid conflicts
    )
