# main.py
from fastapi import FastAPI
from .api import router

app = FastAPI()
app.include_router(router, prefix="/api")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
