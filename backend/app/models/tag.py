from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelORM
from app.models.operation import operation_tag

if TYPE_CHECKING:
    from backend.app.models.operation import OperationORM


class TagORM(BaseModelORM):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    operations: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        secondary=operation_tag,
        back_populates="tags",
    )
