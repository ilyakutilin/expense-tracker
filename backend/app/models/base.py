import re
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, false, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class BaseORM(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        name = cls.__name__
        name = name.replace("ORM", "")
        pattern = re.compile(
            r"""
                (?<=[a-z])      # preceded by lowercase
                (?=[A-Z])       # followed by uppercase
                |               #   OR
                (?<=[A-Z])      # preceded by lowercase
                (?=[A-Z][a-z])  # followed by uppercase, then lowercase
            """,
            re.X,
        )
        return pattern.sub("_", name).lower()

    id_: Mapped[int] = mapped_column(
        "id",
        BigInteger,
        Identity(
            always=True,
            start=1,
            increment=1,
            cycle=False,
        ),
        primary_key=True,
        sort_order=-1,
    )

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

    def __repr__(self):
        """String representation of an ORM Model."""
        cols = []
        for col in self.__table__.columns.keys():
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} ({', '.join(cols)})>"


class UserOwnedBaseORM(BaseORM):
    __abstract__ = True

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), index=True
    )
