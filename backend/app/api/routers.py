from fastapi import APIRouter

from app.api.endpoints import (
    account_router,
    auth_router,
    currency_router,
    tag_router,
    transaction_router,
)

main_router = APIRouter(prefix="/api/v1")
main_router.include_router(currency_router, prefix="/currencies", tags=["Currencies"])
main_router.include_router(account_router, prefix="/accounts", tags=["Accounts"])
main_router.include_router(tag_router, prefix="/tags", tags=["Tags"])
main_router.include_router(
    transaction_router, prefix="/transactions", tags=["Transactions"]
)
main_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
