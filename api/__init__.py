from fastapi import APIRouter
from .tools import router as tools_router
from .meme import router as meme_router
# 如果有其他子模組 user 等也 import 進來

router = APIRouter()
router.include_router(tools_router, prefix="/tools", tags=["tools"])
router.include_router(meme_router, prefix="/memes", tags=["memes"])
# 其他子路由也 include_router
