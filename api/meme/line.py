from fastapi import  APIRouter, FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from schemas.user import userRequest, userResponse

import random
import os

#from supabase import create_client
from dotenv import load_dotenv
import database
#from database import redis_client,supabase

import logging

logger = logging.getLogger(__name__)


from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, ImageMessage, TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

load_dotenv()  # 讀取 .env  >> 測試環境用
router = APIRouter()


configuration = Configuration(
    access_token=os.getenv('LINE_TOKEN')
)
handler = WebhookHandler(os.getenv('LINE_SECRET'))


'''
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)
'''

DEFAULT_MEME_IMAGES = [
    "https://img.zyrastory.com/default/not_found_1.jpeg",
    "https://img.zyrastory.com/default/not_found_2.jpeg",
    "https://img.zyrastory.com/default/not_found_3.jpeg"
]

KEYWORDS = {"股票", "政治", "周星馳"}

'''
API: /callback
功能說明: 供line webhook 呼叫用
'''
@router.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str = Header(None)
):
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    supabase = database.supabase
    redis_client = database.get_redis()

    user_text = event.message.text
    image_url = None
    response = None

    #20251026 新增關鍵字 redis 判斷
    if user_text in KEYWORDS:
        cache_key = f"tag:{user_text}"
        if redis_client.exists(cache_key):
            image_url = redis_client.srandmember(cache_key)
            logger.info('成功從redis取值')
        else:
            response = supabase.rpc(
                'search_meme_by_tag',
                {'search_tag': user_text}
            ).execute()
            logger.info('tag 依然走 rpc')
    else:
        # 使用 RPC 搜尋梗圖  >> rpc 寫法待改 order by random 或許太耗效能
        response = supabase.rpc(
            'search_meme_by_text', 
            {'search_text': user_text}
        ).execute()
    

    # 取得結果
    if response is not None:
        if response.data and len(response.data) > 0:
            meme = response.data[0]
            image_url = meme['image_url']

    if image_url is None:  
        # 沒找到，隨機一筆預設圖
        image_url = random.choice(DEFAULT_MEME_IMAGES)
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    ImageMessage(
                        original_content_url=image_url,
                        preview_image_url=image_url
                    )
                ]
            )
        )

#region API基礎範例 get/post
'''
no: int = Query(..., description="使用者編號")  一般取query string方式
Depends()  >> 把 userRequest 當 callable 呼叫，並自動從 query string 填值
post 不需要 會自動解析
'''

'''
@router.get("/search")
def search_memes(q: str):

    
    response = supabase.table('memes')\
        .select('*')\
        .ilike('content', f'%{q}%')\
        .eq('is_active', True)\
        .order('random')\
        .limit(1)\
        .execute()

    meme = response.data[0] if response.data else None
    
    return {"meme": meme}
'''

@router.get("/example", response_model=userResponse)
def example(user: userRequest = Depends()):
    
    print("in")
    return userResponse(
        no=user.no,
        name=user.name,
        memo="備註範例"
    )

@router.post("/post_example", response_model=userResponse)
def example(user: userRequest):
    
    print("post")
    return userResponse(
        no=user.no,
        name=user.name,
        memo="備註範例_post"
    )
#endregion


#region 工具


#endregion