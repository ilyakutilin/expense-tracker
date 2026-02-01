from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, exists, select, text
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.base import UserOwnedBaseORM

if TYPE_CHECKING:
    from app.models.currency import CurrencyORM
    from app.models.transaction import TransactionLineORM
    from app.models.user import UserORM


class AccountORM(UserOwnedBaseORM):
    name: Mapped[str] = mapped_column(Text)
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), index=True
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"), index=True
    )

    parent: Mapped["AccountORM | None"] = relationship(
        "AccountORM",
        remote_side="AccountORM.id_",
        back_populates="children",
        foreign_keys=[parent_id],
    )

    children: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="accounts",
    )

    transaction_lines: Mapped[list["TransactionLineORM"]] = relationship(
        "TransactionLineORM",
        back_populates="account",
        order_by="desc(TransactionLineORM.id_)",
    )

    user: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="accounts",
    )

    has_children = column_property(
        exists(select(1).where(UserOwnedBaseORM.id_ == parent_id))
    )

    __table_args__ = (
        Index(
            "ix_account_unique_name_per_user_active",
            "user_id",
            "name",
            unique=True,
            postgresql_where=(text("is_deleted = false")),
        ),
        CheckConstraint("id != parent_id", name="account_parent_no_self_reference"),
    )
