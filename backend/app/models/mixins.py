from datetime import datetime

from sqlalchemy import Boolean, DateTime, false, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


class CreatedUpdatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        sort_order=98,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=99,
    )


@declarative_mixin
class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
        index=True,
        sort_order=198,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        sort_order=199,
    )

    @hybrid_property
    def is_active(self) -> bool:  # type: ignore
        return not self.is_deleted

    @is_active.expression  # type: ignore
    def is_active(cls):
        return cls.is_deleted == False  # noqa: E712
