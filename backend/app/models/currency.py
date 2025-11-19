from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import BaseModelNoTimestampsORM

if TYPE_CHECKING:
    from backend.app.models.account import AccountORM
    from backend.app.models.operation import OperationORM


class CurrencyORM(BaseModelNoTimestampsORM):
    __tablename__ = "currency"

    code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
    is_default: Mapped[bool] = mapped_column(default=False)

    accounts: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="currency",
    )

    operations: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        back_populates="currency",
    )
