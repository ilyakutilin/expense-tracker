from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_tag_service
from app.filters.tag import TagFilterParams
from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagCreateUpdate, TagResponse
from app.services import TagService

router = APIRouter()


@router.get("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
async def get_one_tag(
    tag_id: int,
    tag_service: TagService = Depends(get_tag_service),
) -> TagResponse:
    return await tag_service.get_tag_by_id(tag_id)


@router.get(
    "/",
    response_model=PaginatedResponse[TagResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_tags(
    tag_service: TagService = Depends(get_tag_service),
    filter_params: TagFilterParams = Depends(),
    incl_deleted: bool = Query(default=False, description="Include tags in trash"),
) -> PaginatedResponse[TagResponse]:
    return await tag_service.get_all_tags(
        filter_params=filter_params,
        include_deleted=incl_deleted,
    )


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreateUpdate,
    tag_service: TagService = Depends(get_tag_service),
) -> TagResponse:
    return await tag_service.create_tag(tag_data)


@router.patch("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
async def update_tag(
    tag_id: int,
    tag_update: TagCreateUpdate,
    tag_service: TagService = Depends(get_tag_service),
) -> TagResponse:
    return await tag_service.update_tag(tag_id, tag_update)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    perm: bool = False,
    tag_service: TagService = Depends(get_tag_service),
) -> None:
    await tag_service.delete_tag(tag_id, perm)
