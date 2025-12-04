from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseORM
from app.models.mixins import CreatedUpdatedMixin, SoftDeleteMixin
from app.models.operation import operation_tag

if TYPE_CHECKING:
    from app.models.operation import OperationORM


class TagORM(BaseORM, CreatedUpdatedMixin, SoftDeleteMixin):
    name: Mapped[str] = mapped_column(Text, unique=True, index=True)

    operations: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        secondary=operation_tag,
        back_populates="tags",
    )
