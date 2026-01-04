# main.py
from fastapi import FastAPI
from api import router

from contextlib import asynccontextmanager
from core import database

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()   #docker log
    ]
)

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