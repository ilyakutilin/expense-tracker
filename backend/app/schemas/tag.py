from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import StrippedStr


class TagCreateUpdate(BaseModel):
    name: StrippedStr = Field(..., min_length=1, max_length=100)


class TagResponseBase(BaseModel):
    id_: int = Field(serialization_alias="id")
    name: str

    model_config = ConfigDict(from_attributes=True)


class TagResponse(TagResponseBase):
    created_at: datetime
    updated_at: datetime
    transactions_count: int
