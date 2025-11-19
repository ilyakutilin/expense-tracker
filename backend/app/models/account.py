from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelORM

if TYPE_CHECKING:
    from backend.app.models.currency import CurrencyORM


class AccountType(Enum):
    ASSET = "asset"
    INCOME = "income"
    EXPENSE = "expense"

    @classmethod
    def get_values(cls) -> set[str]:
        return {t.value for t in cls}


class AccountORM(BaseModelORM):
    __tablename__ = "account"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    type_: Mapped[str] = mapped_column(
        "type",
        String(50),
        CheckConstraint(
            f"type in {', '.join(AccountType.get_values())}", name="chk_account_type"
        ),
    )
    parent_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("currency.id"))
    balance: Mapped[int]

    parent: Mapped["AccountORM"] = relationship(
        "AccountORM",
        remote_side=[BaseModelORM.id_],
        back_populates="sub_accounts",
        foreign_keys=[parent_id],
    )

    sub_accounts: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="accounts",
    )
