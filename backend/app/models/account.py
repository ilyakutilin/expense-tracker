from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelORM

if TYPE_CHECKING:
    from backend.app.models.currency import CurrencyORM
    from backend.app.models.operation import OperationORM


class AccountType(Enum):
    ASSET = "asset"
    INCOME = "income"
    EXPENSE = "expense"

    @classmethod
    def get_values(cls) -> set[str]:
        return {t.value for t in cls}


class AccountORM(BaseModelORM):
    __tablename__ = "account"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    type_: Mapped[str] = mapped_column(
        "type",
        String(50),
        CheckConstraint(
            f"type in {', '.join(AccountType.get_values())}", name="chk_account_type"
        ),
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), index=True
    )
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"), index=True
    )
    balance: Mapped[int] = mapped_column(default=0)

    parent: Mapped["AccountORM | None"] = relationship(
        "AccountORM",
        remote_side=[BaseModelORM.id_],
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
