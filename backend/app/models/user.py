from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseORM

if TYPE_CHECKING:
    from app.models.account import AccountORM
    from app.models.currency import CurrencyORM
    from app.models.tag import TagORM
    from app.models.transaction import TransactionORM


class UserORM(BaseORM):
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)

    accounts: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="user",
    )

    currencies: Mapped[list["CurrencyORM"]] = relationship(
        "CurrencyORM",
        back_populates="user",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        back_populates="user",
    )

    transactions: Mapped[list["TransactionORM"]] = relationship(
        "TransactionORM",
        back_populates="user",
    )
