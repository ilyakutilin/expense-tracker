from typing import TYPE_CHECKING

from sqlalchemy import Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseORM

if TYPE_CHECKING:
    from app.models.account import AccountORM


class CurrencyORM(BaseORM):
    code: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str | None] = mapped_column(Text)

    accounts: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="currency",
    )

    __table_args__ = (
        Index(
            "ix_currency_unique_code_active",
            "code",
            unique=True,
            postgresql_where=(text("is_deleted = false")),
        ),
    )
