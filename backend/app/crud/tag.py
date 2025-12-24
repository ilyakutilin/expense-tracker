from app.crud.base import CRUDBase
from app.models.tag import TagORM


class CRUDTag(CRUDBase[TagORM]):
    pass


tag_crud = CRUDTag(TagORM)
