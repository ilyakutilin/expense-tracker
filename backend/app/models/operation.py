import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Numeric,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseORM
from app.models.mixins import CreatedUpdatedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.account import AccountORM
    from app.models.tag import TagORM


operation_tag = Table(
    "operation_tag",
    BaseORM.metadata,
    Column("operation_id", ForeignKey("operation.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class OperationORM(BaseORM, CreatedUpdatedMixin, SoftDeleteMixin):
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    from_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    to_acc_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT"), index=True
    )
    from_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=23, scale=8, decimal_return_scale=8, asdecimal=True)
    )
    to_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=23, scale=8, decimal_return_scale=8, asdecimal=True)
    )
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    comment: Mapped[str] = mapped_column(Text, default="", index=True)
    is_template: Mapped[bool] = mapped_column(default=False, index=True)

    from_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[from_acc_id],
        back_populates="operations_from",
    )

    to_acc: Mapped["AccountORM"] = relationship(
        "AccountORM",
        foreign_keys=[to_acc_id],
        back_populates="operations_to",
    )

    tags: Mapped[list["TagORM"]] = relationship(
        "TagORM",
        secondary=operation_tag,
        back_populates="operations",
        lazy="selectin",
    )
