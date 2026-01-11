# main.py
from fastapi import FastAPI
from api import router

from contextlib import asynccontextmanager
from core import database

from core.logger import logger

# 已經在 core.logger 中完成初始化，這裡不需要 basicConfig
logger.info("Starting Zyrastory API...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_connections()
    yield
    database.close_connections()

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)