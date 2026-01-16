from enum import Enum

from pydantic import BaseModel


class Entity(str, Enum):
    ACCOUNT = "account"
    CURRENCY = "currency"
    TAG = "tag"
    TRANSACTION = "transaction"


class Type(str, Enum):
    DETAIL = "detail"
    LIST = "list"


class CachePattern(BaseModel):
    entity: Entity
    obj_id_key: str | None
    is_user_owned: bool = True

    def __str__(self) -> str:
        parts: list[str] = [self.entity.value]

        parts.append(
            Type.DETAIL.value if self.obj_id_key is not None else Type.LIST.value
        )

        if self.is_user_owned:
            parts.append("user_id={user_id}")

        if self.obj_id_key:
            parts.append("%s={%s}" % (self.obj_id_key, self.obj_id_key))

        return ":".join(parts)
