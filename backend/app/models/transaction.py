import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, ForeignKey, Numeric, Table, Text, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.settings import settings
from app.models.base import BaseFilter, BaseORM

if TYPE_CHECKING:
    from app.models.account import AccountORM
    from app.models.tag import TagORM


transaction_tag = Table(
    "transaction_tag",
    BaseORM.metadata,
    Column("transaction_id", ForeignKey("transaction.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class TransactionORM(BaseORM):
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    from_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    to_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    from_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=settings.NUMERIC_PRECISION,
            scale=settings.NUMERIC_SCALE,
            decimal_return_scale=settings.NUMERIC_SCALE,
            asdecimal=True,
        )
    )
    to_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=settings.NUMERIC_PRECISION,
            scale=settings.NUMERIC_SCALE,
            decimal_return_scale=settings.NUMERIC_SCALE,
            asdecimal=True,
        )
    )
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    comment: Mapped[str | None] = mapped_column(Text, index=True)
    is_template: Mapped[bool] = mapped_column(server_default=false(), index=True)

    from_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[from_acc_id],
        back_populates="transactions_from",
    )

    to_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[to_acc_id],
        back_populates="transactions_to",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        secondary=transaction_tag,
        back_populates="transactions",
        lazy="selectin",
    )


class TransactionFilter(BaseFilter):
    order_by: list[str] = ["id"]
    search: str | None = None

    class Constants(BaseFilter.Constants):
        model = TransactionORM
        search_model_fields = ["comment"]

    # TODO: Complete TransactionFilter
