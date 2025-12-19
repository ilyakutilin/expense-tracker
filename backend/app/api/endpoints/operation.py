from fastapi import APIRouter, Depends, Query, status
from fastapi_filter import FilterDepends

from app.api.deps import get_operation_service
from app.models.operation import OperationFilter
from app.schemas.operation import OperationCreate, OperationResponse, OperationUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import OperationService

router = APIRouter()


@router.get(
    "/{operation_id}", response_model=OperationResponse, status_code=status.HTTP_200_OK
)
async def get_one_operation(
    operation_id: int,
    operation_service: OperationService = Depends(get_operation_service),
) -> OperationResponse:
    return await operation_service.get_operation_by_id(operation_id)


@router.get(
    "/",
    response_model=PaginatedResponse[OperationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_operations(
    operation_service: OperationService = Depends(get_operation_service),
    operation_filter: OperationFilter = FilterDepends(OperationFilter, by_alias=True),
    incl_deleted: bool = Query(
        default=False, description="Include operations in trash"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[OperationResponse]:
    return await operation_service.get_all_operations(
        include_deleted=incl_deleted,
        filter_=operation_filter,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_operation(
    operation_data: OperationCreate,
    operation_service: OperationService = Depends(get_operation_service),
) -> OperationResponse:
    return await operation_service.create_operation(operation_data)


@router.patch(
    "/{operation_id}", response_model=OperationResponse, status_code=status.HTTP_200_OK
)
async def update_operation(
    operation_id: int,
    operation_update: OperationUpdate,
    operation_service: OperationService = Depends(get_operation_service),
) -> OperationResponse:
    return await operation_service.update_operation(operation_id, operation_update)


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operation(
    operation_id: int,
    perm: bool = False,
    operation_service: OperationService = Depends(get_operation_service),
) -> None:
    await operation_service.delete_operation(operation_id, perm)
