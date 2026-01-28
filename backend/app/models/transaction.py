import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Numeric,
    Table,
    Text,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.settings import settings
from app.models.base import BaseORM, UserOwnedBaseORM

if TYPE_CHECKING:
    from app.models.account import AccountORM
    from app.models.tag import TagORM
    from app.models.user import UserORM


transaction_tag = Table(
    "transaction_tag",
    BaseORM.metadata,
    Column("transaction_id", ForeignKey("transaction.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class TransactionORM(UserOwnedBaseORM):
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    comment: Mapped[str | None] = mapped_column(Text, index=True)
    is_template: Mapped[bool] = mapped_column(server_default=false(), index=True)

    lines: Mapped[list["TransactionLineORM"]] = relationship(
        "TransactionLineORM",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        secondary=transaction_tag,
        back_populates="transactions",
    )

    user: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="transactions",
    )

    __table_args__ = (
        # Index for filtering active transactions in joins
        Index(
            "ix_transaction_user_active",
            "user_id",
            "id",
            postgresql_where=(text("(is_deleted = false) AND (is_template = false)")),
        ),
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
        # Composite index for balance queries - most important!
        Index(
            "ix_transaction_line_account_transaction",
            "account_id",
            "transaction_id",
            postgresql_where=(text("is_deleted = false")),
        ),
    )
