from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, List
from schemas.base import CommaInt
from datetime import datetime

class MemeSearchRequest(BaseModel):
    page: int = Field(..., ge=1)                #Greater than or Equal to / Less than or Equal to 也就是直接在模型驗證數值大於小於
    page_size: int = Field(..., ge=1, le=200)
    content: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[str] = None


class MemeResponse(BaseModel):
    id: int
    content: str
    image_url: str
    tags: List[str]                # TEXT[] 會變成 list[str]
    is_active: bool
    created_at: datetime

    @field_validator("tags", mode="before") #before 取原始值
    @classmethod
    def normalize_tags(cls, v):
        return v or []              # A or B 要是falsy 回傳 []  (None False 0 這些都算)

class MemeSearchResponse(BaseModel):
    data: List[MemeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MemeUpdateRequest(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None