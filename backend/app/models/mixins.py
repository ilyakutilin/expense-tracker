from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column


class CreatedUpdatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        sort_order=98,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        sort_order=99,
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        sort_order=198,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        sort_order=199,
    )

    @hybrid_property
    def is_active(self) -> bool:
        return not self.is_deleted
