from fastapi import APIRouter
from .image_tool import router as image_tool_router

router = APIRouter()
router.include_router(image_tool_router, prefix="/image_tool", tags=["image_tool"])