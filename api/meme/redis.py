'''
更新 redis cache 用
'''

from fastapi import  APIRouter, FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from schemas.base import ApiResponse
import os

from dotenv import load_dotenv
#from database import redis_client,supabase
import database

load_dotenv() 

router = APIRouter()
KEYWORDS = {"股票", "政治", "周星馳"}


@router.post("/update-tag/{tag}")
async def refresh_tag_cache(tag: str, authorization: str = Header(None)):
    verify_admin(authorization)

    supabase = database.supabase
    redis_client = database.redis_client
    
    if tag not in KEYWORDS:
        raise HTTPException(400, detail=f"Invalid tag: {tag}")
    
    cache_key = f"tag:{tag}"
    message = ''

    try:
        #只刪除存在的
        if redis_client.exists(cache_key):
            redis_client.delete(cache_key)
            message += 'delete and '

        response = supabase.rpc('search_memes_by_tag', {'search_tag': tag}).execute()
        if response.data:
            urls = [m['image_url'] for m in response.data]
            redis_client.sadd(cache_key, *urls)
            message += 'build'

            return ApiResponse(status="success",message=message)
        else:
            return ApiResponse(status="faild",message="no Data found")
        
    except Exception as e:
        return ApiResponse(status="failed",message=str(e))


'''基本驗證'''
def verify_admin(authorization: str):
    admin_token = os.getenv('ADMIN_TOKEN')
    if authorization != f"Bearer {admin_token}":
        raise HTTPException(403, detail="Forbidden")