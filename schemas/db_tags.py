"""
Database Tag Statistics Schema
用於 Dashboard 顯示 DB 中 Tag 對應的梗圖數量
"""

from pydantic import BaseModel
from typing import List


class DbTagCount(BaseModel):
    """單一 Tag 的統計資料"""
    tag_name: str
    count: int


class DbTagsResponse(BaseModel):
    """DB Tag 統計 API 回應"""
    tags: List[DbTagCount]
    total_tags: int
