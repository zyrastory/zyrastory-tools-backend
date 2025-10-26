from supabase import create_client
import redis
import os

from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

redis_client = None
supabase = None

KEYWORDS = {"股票", "政治", "周星馳"}

"""初始化所有連線"""
def init_connections():

    load_dotenv()  # 讀取 .env  >> 測試環境用
    global redis_client, supabase
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Redis init success")
        print("Redis connected")

        init_cache()

    except Exception as e:
        logger.error(f"Redis init failed: {e}")
        print(f"Redis init failed: {e}")
        redis_client = None

"""關閉連線"""
def close_connections():
    global redis_client, supabase
    if redis_client:
        redis_client.close()


def init_cache():
    global redis_client, supabase
    if not redis_client:
        return
    
    logger.info("Redis initialize...")
    print("Redis initialize...")
    
    for tag in KEYWORDS:
        cache_key = f"tag:{tag}"
        
        # 已有快取就跳過 >> 手動呼叫 redis 更新即可
        if redis_client.exists(cache_key):
            print(f"Cache exists: {tag}")
            continue
        
        # 從 DB 載入
        response = supabase.rpc('search_memes_by_tag', {'search_tag': tag}).execute()
        
        if response.data:
            urls = [m['image_url'] for m in response.data]
            logger.info(f"Redis before add: {tag} ")
            redis_client.sadd(cache_key, *urls)
            #redis_client.expire(cache_key, 86400)  # 24小時

            print(f"Redis add: {tag} ({len(urls)} memes)")
            logger.info(f"Redis add: {tag} ({len(urls)} memes)")
        else:
            print(f"no memes for: {tag}")

def get_redis():
    global redis_client, supabase
    try:
        redis_client.ping()
    except (redis.exceptions.ConnectionError, BrokenPipeError):
        logger.info("Redis connection lost, reconnecting...")
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            decode_responses=True
        )
    return redis_client