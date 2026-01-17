from pydantic import BaseModel
from typing import List

class RedisTagInspection(BaseModel):
    """單一 tag 的 Redis 一致性檢查結果"""
    tag_name: str
    zset_count: int  # ZSET tag_count 中的數量
    set_count: int   # SET tag:* 中的實際 URL 數量
    is_consistent: bool  # 是否一致
    difference: int  # 差異值 (zset_count - set_count)

class RedisInspectResponse(BaseModel):
    """Redis 一致性檢查完整報告"""
    total_tags: int
    consistent_count: int
    inconsistent_count: int
    inspections: List[RedisTagInspection]
