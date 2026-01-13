from typing import TYPE_CHECKING

from sqlalchemy import Index, Text, func, select, text
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.base import UserOwnedBaseORM
from app.models.transaction import transaction_tag

if TYPE_CHECKING:
    from app.models.transaction import TransactionORM
    from app.models.user import UserORM


class TagORM(UserOwnedBaseORM):
    name: Mapped[str] = mapped_column(Text)

    transactions: Mapped[list["TransactionORM"]] = relationship(
        "TransactionORM",
        secondary=transaction_tag,
        back_populates="tags",
    )

    transactions_count: Mapped[int] = column_property(
        select(func.count(transaction_tag.c.tag_id))
        .where(transaction_tag.c.tag_id == UserOwnedBaseORM.id_)
        .correlate_except(transaction_tag)
        .scalar_subquery()
    )

    user: Mapped["UserORM | None"] = relationship(
        "UserORM",
        back_populates="tags",
    )

    __table_args__ = (
        Index(
            "ix_tag_unique_name_per_user_active",
            "user_id",
            "name",
            unique=True,
            postgresql_where=(text("is_deleted = false")),
        ),
    )
