from app.crud.base import CRUDBase
from app.models.user import UserORM


class CRUDUser(CRUDBase[UserORM]):
    pass


user_crud = CRUDUser(UserORM)
