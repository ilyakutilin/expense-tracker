from datetime import datetime
from typing import Union

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer
from sqlalchemy import BigInteger, Boolean, DateTime, Identity, false, func, or_
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, Query, declared_attr, mapped_column
from sqlalchemy.sql.selectable import Select


class BaseORM(AsyncAttrs, DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower().replace("orm", "")

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


class BaseFilter(Filter):
    @property
    def ordering_values(self):
        raw_values = super().ordering_values
        processed_values = []
        aliased_fields = ["id", "type"]
        for v in raw_values:
            if isinstance(v, str) and v in aliased_fields:
                processed_values.append(f"{v}_")
            else:
                processed_values.append(v)
        return processed_values

    def filter(self, query: Union[Query, Select]):
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Filter):
                query = field_value.filter(query)
            else:
                if "__" in field_name:
                    field_name, operator = field_name.split("__")
                    if field_name in ["id", "type"]:
                        field_name = f"{field_name}_"
                    operator, value = _orm_operator_transformer[operator](value)
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):
                    search_filters = [
                        getattr(self.Constants.model, field).ilike(f"%{value}%")
                        for field in self.Constants.search_model_fields
                    ]
                    query = query.filter(or_(*search_filters))
                else:
                    model_field = getattr(self.Constants.model, field_name)
                    query = query.filter(getattr(model_field, operator)(value))

        return query
