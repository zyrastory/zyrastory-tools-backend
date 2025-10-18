from fastapi import APIRouter
from .line import router as line_router

router = APIRouter()
router.include_router(line_router, prefix="", tags=["line_meme"])