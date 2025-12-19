from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy import Index, Text, func, select, text
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.base import BaseFilter, BaseORM
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


class TagFilter(BaseFilter):
    order_by: list[str] = ["id"]
    search: str | None = None

    class Constants(BaseFilter.Constants):
        model = TagORM
        search_model_fields = ["name"]

    @field_validator("order_by")
    def restrict_sortable_fields(cls, value):
        if value is None:
            return None

        allowed_field_names = [
            "id",
            "name",
            "created_at",
            "updated_at",
            "operations_count",
        ]

        for field_name in value:
            field_name = field_name.replace("+", "").replace("-", "")
            if field_name not in allowed_field_names:
                raise ValueError(
                    f"You may only sort by: {', '.join(allowed_field_names)}"
                )

        return value
