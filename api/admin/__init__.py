from fastapi import APIRouter
from .admin import login_router,admin_router
# 如果有其他子模組 user 等也 import 進來

router = APIRouter()
router.include_router(login_router, prefix="", tags=["login"])
router.include_router(admin_router, prefix="", tags=["admin"])
# 其他子路由也 include_router
