from app.api.endpoints.account import router as account_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.currency import router as currency_router
from app.api.endpoints.tag import router as tag_router
from app.api.endpoints.transaction import router as transaction_router
from app.api.endpoints.user import router as user_router

__all__ = [
    "currency_router",
    "account_router",
    "tag_router",
    "transaction_router",
    "auth_router",
    "user_router",
]
