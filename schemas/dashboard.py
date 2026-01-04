from pydantic import BaseModel
from typing import List
from schemas.base import CommaInt

class redis_tag_count(BaseModel):
    tag_name: str
    count: int

class dashboardResponse(BaseModel):
    total_count: CommaInt
    tag_counts: List[redis_tag_count]
