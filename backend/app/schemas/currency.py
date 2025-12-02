from pydantic import BaseModel, ConfigDict, Field


class CurrencyCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=5)
    symbol: str | None = Field(None, min_length=1, max_length=1)


class CurrencyDB(CurrencyCreate):
    id_: int

    model_config = ConfigDict(from_attributes=True)
