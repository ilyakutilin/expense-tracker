from typing import TYPE_CHECKING

from sqlalchemy import Index, Text, func, select, text
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.base import BaseORM
from app.models.operation import operation_tag

if TYPE_CHECKING:
    from app.models.operation import OperationORM


class TagORM(BaseORM):
    name: Mapped[str] = mapped_column(Text)

    operations: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        secondary=operation_tag,
        back_populates="tags",
    )

    operations_count: Mapped[int] = column_property(
        select(func.count(operation_tag.c.tag_id))
        .where(operation_tag.c.tag_id == BaseORM.id_)
        .correlate_except(operation_tag)
        .scalar_subquery()
    )

    __table_args__ = (
        Index(
            "ix_tag_unique_name_active",
            "name",
            unique=True,
            postgresql_where=(text("is_deleted = false")),
        ),
    )
