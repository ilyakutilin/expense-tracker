from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import BaseModelNoTimestampsORM

if TYPE_CHECKING:
    from backend.app.models.account import AccountORM


class CurrencyORM(BaseModelNoTimestampsORM):
    __tablename__ = "currency"

    code: Mapped[str] = mapped_column(String(5), unique=True, index=True)

    accounts: Mapped["AccountORM"] = relationship(
        "AccountORM", back_populates="currency"
    )
