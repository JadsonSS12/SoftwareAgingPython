from pydantic import BaseModel, Field

class Item(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(..., example="example item")
    description: str = Field(None, example="optional description")
