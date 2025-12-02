from fastapi import APIRouter

from app.api.endpoints import currency_router

main_router = APIRouter()
main_router.include_router(currency_router, prefix="/currencies", tags=["Currencies"])
