from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreateUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TagResponse(BaseModel):
    id_: int = Field(serialization_alias="id")
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
