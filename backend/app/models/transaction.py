import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, ForeignKey, Index, Numeric, Table, Text, false
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
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    comment: Mapped[str | None] = mapped_column(Text, index=True)
    is_template: Mapped[bool] = mapped_column(server_default=false(), index=True)

    lines: Mapped[list["TransactionLineORM"]] = relationship(
        "TransactionLineORM",
        back_populates="transaction",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        secondary=transaction_tag,
        back_populates="transactions",
        lazy="selectin",
    )


class TransactionLineORM(BaseORM):
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transaction.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=settings.NUMERIC_PRECISION,
            scale=settings.NUMERIC_SCALE,
            decimal_return_scale=settings.NUMERIC_SCALE,
            asdecimal=True,
        )
    )

    transaction: Mapped["AccountORM"] = relationship(
        "TransactionORM",
        back_populates="lines",
    )

    account: Mapped["AccountORM"] = relationship(
        "AccountORM",
        back_populates="transaction_lines",
    )

    __table_args__ = (
        Index("ix_transaction_line_account_date", "account_id", "transaction_id"),
    )


class TransactionFilter(BaseFilter):
    order_by: list[str] = ["id"]
    search: str | None = None

    class Constants(BaseFilter.Constants):
        model = TransactionORM
        search_model_fields = ["comment"]

    # TODO: Complete TransactionFilter
