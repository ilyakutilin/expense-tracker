from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression

from app.core import exceptions as exc
from app.models.base import BaseORM

ModelType = TypeVar("ModelType", bound="BaseORM")


class FilterOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    ILIKE = "ilike"


@dataclass
class FilterConditions:
    """Container for filter conditions that can be applied to queries"""

    where_clauses: list[ColumnElement[bool]]
    order_by_clauses: list[UnaryExpression]
    offset_limit: tuple[int, int]

    def has_filters(self) -> bool:
        """Check if any filter conditions exist"""
        return len(self.where_clauses) > 0

    def has_ordering(self) -> bool:
        """Check if any ordering exists"""
        return len(self.order_by_clauses) > 0

    def has_pagination(self) -> bool:
        """Check if pagination params are set"""
        return bool(self.offset_limit)


class BaseFilterParams(BaseModel):
    """Base class for filter parameters"""

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Multi-field ordering with - prefix for DESC
    order_by: str | None = Field(
        None, description="Comma-separated fields, prefix with - for DESC"
    )

    # Search
    search: str | None = Field(None, description="Search term")

    def get_offset(self) -> int:
        """Calculate SQL offset from page number"""
        return (self.page - 1) * self.page_size

    def parse_order_by(self) -> list[tuple[str, str]]:
        """
        Parse order_by string into list of (field, direction) tuples
        Example: "-date,id" -> [("date", "desc"), ("id", "asc")]
        """
        if not self.order_by:
            return []

        result = []
        for field in self.order_by.split(","):
            field = field.strip()
            if field.startswith("-"):
                result.append((field[1:], "desc"))
            else:
                result.append((field, "asc"))
        return result


class FilterField:
    """Defines how a filter field should be processed"""

    def __init__(
        self,
        column: InstrumentedAttribute | None = None,
        operator: FilterOperator = FilterOperator.EQ,
        preprocessor: Callable | None = None,
        subquery_builder: Callable | None = None,
    ):
        self.column = column
        self.operator = operator
        self.preprocessor = preprocessor
        self.subquery_builder = subquery_builder

    def build_condition(
        self, value: Any, model_class: type[ModelType]
    ) -> ColumnElement[bool] | None:
        """Build a WHERE condition for this filter"""
        if value is None:
            return None

        if self.preprocessor:
            value = self.preprocessor(value)

        if self.subquery_builder:
            return self.subquery_builder(value, model_class)

        if not self.column:
            raise exc.CodeError(
                (
                    "While building a FilterField neither a column nor a "
                    "subquery_builder was given"
                )
            )

        match self.operator:
            case FilterOperator.EQ:
                return self.column == value
            case FilterOperator.NE:
                return self.column != value
            case FilterOperator.GT:
                return self.column > value
            case FilterOperator.GTE:
                return self.column >= value
            case FilterOperator.LT:
                return self.column < value
            case FilterOperator.LTE:
                return self.column <= value
            case FilterOperator.IN:
                return self.column.in_(value)
            case FilterOperator.LIKE:
                return self.column.like(f"%{value}%")
            case FilterOperator.ILIKE:
                return self.column.ilike(f"%{value}%")

        return None


class OrderField:
    """Defines how an order field should be processed"""

    def __init__(
        self,
        column: InstrumentedAttribute | None = None,
        subquery_builder: Callable | None = None,
    ):
        self.column = column
        self.subquery_builder = subquery_builder

    def build_order_clause(self, direction: str, model_class: Any) -> UnaryExpression:
        """Build an ORDER BY clause"""
        order_func = desc if direction == "desc" else asc

        if self.subquery_builder:
            return order_func(self.subquery_builder(model_class))

        if not self.column:
            raise exc.CodeError(
                (
                    "While building an OrderField neither a column nor a "
                    "subquery_builder was given"
                )
            )

        return order_func(self.column)


class SearchField:
    """Defines a field that can be searched"""

    def __init__(self, column: InstrumentedAttribute):
        self.column = column

    def build_condition(self, search_term: str) -> ColumnElement[bool]:
        """Build a search condition"""
        return self.column.ilike(f"%{search_term}%")


class FilterManager:
    """Manages the building of filter conditions"""

    def __init__(
        self,
        model_class: Any,
        filter_fields: dict[str, FilterField],
        order_fields: dict[str, OrderField],
        search_fields: list[SearchField],
    ):
        self.model_class = model_class
        self.filter_fields = filter_fields
        self.order_fields = order_fields
        self.search_fields = search_fields

    def build_conditions(self, params: BaseFilterParams) -> FilterConditions:
        """
        Build filter and order conditions from parameters
        Returns FilterConditions that can be applied to any query
        """
        where_clauses = []
        order_by_clauses = []

        # Build filter conditions
        for field_name, filter_field in self.filter_fields.items():
            value = getattr(params, field_name, None)
            if value is not None:
                condition = filter_field.build_condition(value, self.model_class)
                if condition is not None:
                    where_clauses.append(condition)

        # Build search conditions
        if params.search and self.search_fields:
            search_conditions = [
                field.build_condition(params.search) for field in self.search_fields
            ]
            where_clauses.append(or_(*search_conditions))

        # Build order conditions
        order_fields = params.parse_order_by()
        for field_name, direction in order_fields:
            if field_name in self.order_fields:
                order_field = self.order_fields[field_name]
                order_clause = order_field.build_order_clause(
                    direction, self.model_class
                )
                order_by_clauses.append(order_clause)

        return FilterConditions(
            where_clauses=where_clauses,
            order_by_clauses=order_by_clauses,
            offset_limit=(params.get_offset(), params.page_size),
        )
