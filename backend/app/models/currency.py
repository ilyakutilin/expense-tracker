from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseORM

if TYPE_CHECKING:
    from app.models.account import AccountORM


class CurrencyORM(BaseORM):
    code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    symbol: Mapped[str | None] = mapped_column(Text)

    accounts: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="currency",
    )
