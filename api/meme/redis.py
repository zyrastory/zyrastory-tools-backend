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

import logging

logger = logging.getLogger(__name__)

load_dotenv() 

router = APIRouter()
#KEYWORDS = {"股票", "政治", "周星馳"}


@router.post("/update-tag/{tag}")
async def refresh_tag_cache(tag: str, authorization: str = Header(None)):
    verify_admin(authorization)

    supabase = database.supabase
    redis_client = database.redis_client
    redis_tags = database.redis_tags
    
    if tag not in redis_tags:
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


@router.post("/update-all-tag")
async def refresh_all_tag_cache( authorization: str = Header(None)):
    verify_admin(authorization)

    supabase = database.supabase
    redis_client = database.redis_client
    
    message = ''

    try:
        # now redis
        redis_result = {}
        for key in redis_client.scan_iter("tag:*"):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            redis_result[key_str] = redis_client.scard(key_str)

        # DB count
        count_response = supabase.rpc('get_tag_counts').execute()

        if count_response.data:
            #20251202 新增，API可直接更新tag
            new_tags = {row["tag"] for row in count_response.data if row.get("tag")}
            database.set_redis_tag(new_tags)

            for row in count_response.data:
                tag = row["tag"]
                db_count = row["count"]
                cache_key = f"tag:{tag}"

                #20251208 新增tag數量 zset統計 (供 /count 使用)
                redis_client.zadd("tag_count", {row["tag"]: row["count"]})

                response = None

                if cache_key in redis_result:
                    redis_count = redis_result[cache_key]
                    if redis_count != db_count:
                        msg = f"tag {tag} count - reids:{redis_count}, db:{db_count}"
                        logger.info(msg)
                        redis_client.delete(cache_key)
                        response = supabase.rpc('search_memes_by_tag', {'search_tag': tag}).execute()

                        message+=msg
                
                #不存在redis的
                else:
                    response = supabase.rpc('search_memes_by_tag', {'search_tag': tag}).execute()
                    message+=f"tag {tag} not in redis now"
                
                if response is not None and response.data:
                    urls = [m['image_url'] for m in response.data]
                    redis_client.sadd(cache_key, *urls)
                    #redis_client.expire(cache_key, 86400)  # 24小時
                    #logger.info(f"Redis add: {tag} ({len(urls)} memes)")
                    message+="  -  success\n"
            
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