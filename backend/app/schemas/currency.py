from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from app.schemas import StrippedStr


class CurrencyCreate(BaseModel):
    code: StrippedStr = Field(..., min_length=3, max_length=5)
    symbol: StrippedStr | None = Field(None, min_length=1, max_length=1)


class CurrencyUpdate(CurrencyCreate):
    code: StrippedStr | None = Field(None, min_length=3, max_length=5)


class CurrencyResponse(CurrencyCreate):
    id_: int = Field(serialization_alias="id")

    model_config = ConfigDict(from_attributes=True)

    @model_serializer(mode="wrap")
    def sort_keys(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        serialized: dict[str, Any] = handler(self)
        id_field_name = "id"
        if any([k.endswith("_") for k in serialized]):
            id_field_name = "id_"

        key_order = [id_field_name, "code", "symbol"]
        return {k: serialized[k] for k in key_order}
