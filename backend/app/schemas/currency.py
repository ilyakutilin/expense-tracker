from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)


class CurrencyCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=5)
    symbol: str | None = Field(None, min_length=1, max_length=1)


class CurrencyUpdate(CurrencyCreate):
    code: str | None = Field(None, min_length=3, max_length=5)


class CurrencyResponse(CurrencyCreate):
    id_: int = Field(serialization_alias="id")

    model_config = ConfigDict(from_attributes=True)

    @model_serializer(mode="wrap")
    def sort_keys(self, handler: SerializerFunctionWrapHandler) -> dict[str, int | str]:
        serialized = handler(self)
        key_order = ["id", "code", "symbol"]
        return {k: serialized[k] for k in key_order}
