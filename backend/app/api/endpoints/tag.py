from fastapi import APIRouter, Depends, status

# from fastapi import Query
# from fastapi_filter import FilterDepends
from app.api.deps import get_tag_service

# from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagCreateUpdate, TagResponse
from app.services import TagService

router = APIRouter()


# @router.get("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
# async def get_one_tag(
#     tag_id: int,
#     tag_service: TagService = Depends(get_tag_service),
# ) -> TagResponse:
#     return await tag_service.get_tag_by_id(tag_id)


# @router.get(
#     "/",
#     response_model=PaginatedResponse[TagResponse],
#     status_code=status.HTTP_200_OK,
# )
# async def get_all_tags(
#     tag_service: TagService = Depends(get_tag_service),
#     tag_filter: TagFilter = FilterDepends(TagFilter, by_alias=True),
#     incl_deleted: bool = Query(default=False, description="Include tags in trash"),
#     page: int = Query(default=1, ge=1, description="Page number"),
#     page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
# ) -> PaginatedResponse[TagResponse]:
#     return PaginatedResponse(
#         total=0,
#         page=0,
#         page_size=0,
#         total_pages=0,
#         items=[],
#     )


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreateUpdate,
    tag_service: TagService = Depends(get_tag_service),
) -> TagResponse:
    return await tag_service.create_tag(tag_data)


# @router.patch("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
# async def update_tag(
#     tag_id: int,
#     tag_update: TagCreateUpdate,
#     tag_service: TagService = Depends(get_tag_service),
# ) -> TagResponse:
#     return await tag_service.update_tag(tag_id, tag_update)


# @router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_tag(
#     tag_id: int,
#     perm: bool = False,
#     tag_service: TagService = Depends(get_tag_service),
# ) -> None:
#     await tag_service.delete_tag(tag_id, perm)
