from pydantic import BaseModel
from typing import List, Dict
from schemas.base import CommaInt

class RedisTagCount(BaseModel):
    tag_name: str
    count: CommaInt  # 使用 CommaInt 顯示千位分隔

class HotKeyword(BaseModel):
    keyword: str
    count: CommaInt  # 使用 CommaInt 顯示千位分隔

class DbTagCount(BaseModel):
    tag_name: str
    count: CommaInt  # 使用 CommaInt 顯示千位分隔

class DashboardResponse(BaseModel):
    meme_total_count: CommaInt
    tags_total_count: CommaInt
    tag_counts: List[RedisTagCount]
    today_calls: CommaInt
    today_images: CommaInt
    total_images_served: CommaInt
    hot_keywords: List[HotKeyword]
    db_tag_counts: List[DbTagCount]  # 新增：資料庫 Tag 統計
