from datetime import datetime

from pydantic import ConfigDict

from app.filters.base import (
    BaseFilterParams,
    FilterField,
    FilterManager,
    FilterOperator,
    OrderField,
    SearchField,
)
from app.models.user import UserORM
from app.schemas.user import UserRole

user_filter_manager = FilterManager(
    model_class=UserORM,
    filter_fields={
        "email": FilterField(column=UserORM.email, operator=FilterOperator.ILIKE),
        "role": FilterField(column=UserORM.role, operator=FilterOperator.EQ),
        "created_at_lte": FilterField(
            column=UserORM.created_at, operator=FilterOperator.LTE
        ),
        "created_at_gte": FilterField(
            column=UserORM.created_at, operator=FilterOperator.GTE
        ),
        "updated_at_lte": FilterField(
            column=UserORM.updated_at, operator=FilterOperator.LTE
        ),
        "updated_at_gte": FilterField(
            column=UserORM.updated_at, operator=FilterOperator.GTE
        ),
        "is_deleted": FilterField(
            column=UserORM.is_deleted, operator=FilterOperator.EQ
        ),
        "deleted_at_lte": FilterField(
            column=UserORM.deleted_at, operator=FilterOperator.LTE
        ),
        "deleted_at_gte": FilterField(
            column=UserORM.deleted_at, operator=FilterOperator.GTE
        ),
    },
    order_fields={
        "id": OrderField(column=UserORM.id_),
        "email": OrderField(column=UserORM.email),
        "role": OrderField(column=UserORM.role),
        "created_at": OrderField(column=UserORM.created_at),
        "updated_at": OrderField(column=UserORM.updated_at),
        "is_deleted": OrderField(column=UserORM.is_deleted),
        "deleted_at": OrderField(column=UserORM.deleted_at),
    },
    search_fields=[
        SearchField(column=UserORM.email),
    ],
)


class UserFilterParams(BaseFilterParams):
    """Filter parameters for users"""

    email: str | None = None
    role: UserRole | None = None
    created_at_lte: datetime | None = None
    created_at_gte: datetime | None = None
    updated_at_lte: datetime | None = None
    updated_at_gte: datetime | None = None
    is_deleted: bool | None = None
    deleted_at_lte: datetime | None = None
    deleted_at_gte: datetime | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def manager(self) -> FilterManager:
        return user_filter_manager
