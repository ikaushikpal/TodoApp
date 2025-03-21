from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Annotated, Optional

from app.models.todo import Todo

def strip_whitespace(v: str) -> str:
    """Strip leading and trailing whitespace from a string."""
    return v.strip() if isinstance(v, str) else v

class TodoCreate(BaseModel):
    title: Annotated[
        str, Field(..., min_length=3, max_length=50, example="Buy groceries")
    ]
    description: Annotated[
        Optional[str], Field(None, max_length=500, example="Milk, eggs, bread")
    ]
    priority: Annotated[int, Field(..., ge=1, le=5, example=3)]

    @field_validator('title', 'description')
    @classmethod
    def strip_and_validate(cls, v):
        v = strip_whitespace(v)
        return v


class TodoUpdate(BaseModel):
    title: Annotated[
        str, Field(..., min_length=3, max_length=50, example="Buy groceries")
    ]
    description: Annotated[
        Optional[str], Field(None, max_length=500, example="Milk, eggs, bread")
    ]
    priority: Annotated[int, Field(..., ge=1, le=5, example=3)]
    complete: Annotated[bool, Field(..., example=True)]

    @field_validator('title', 'description')
    @classmethod
    def strip_and_validate(cls, v):
        v = strip_whitespace(v)
        return v


class TodoResponse(BaseModel):
    id: int = Field(..., example=1)
    title: str = Field(..., example="Buy groceries")
    description: Optional[str] = Field(None, example="Milk, eggs, bread")
    priority: int = Field(..., example=3)
    complete: bool = Field(..., example=False)
    owner_id: Annotated[
        str,
        Field(
            min_length=36,
            max_length=36,
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]
    created_at: datetime = Field(..., example="2025-03-16T10:00:00Z")
    finished_at: Optional[datetime] = Field(None, example="2025-03-18T12:00:00Z")

    model_config = {
        "from_attributes": True
    }  # Replaces Config class for ORM compatibility
