from pydantic import BaseModel
from typing import List
from schemas.base import CommaInt

class RedisTagCount(BaseModel):
    tag_name: str
    count: int

class DashboardResponse(BaseModel):
    total_count: CommaInt
    tag_counts: List[RedisTagCount]
