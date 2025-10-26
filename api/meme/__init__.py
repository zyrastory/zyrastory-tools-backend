from fastapi import APIRouter
from .line import router as line_router
from .redis import router as redis_router

router = APIRouter()
router.include_router(line_router, prefix="", tags=["line_meme"])
router.include_router(redis_router, prefix="/cache", tags=["cache"])