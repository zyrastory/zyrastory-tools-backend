from fastapi import  APIRouter, FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from schemas.user import userRequest, userResponse

import random
import os

from supabase import create_client
from dotenv import load_dotenv

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
API: /upload
功能說明: 
'''
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

DEFAULT_MEME_IMAGES = [
    "https://img.zyrastory.com/not_found_1.jpeg",
    "https://img.zyrastory.com/not_found_2.jpeg"
]

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
    user_text = event.message.text
    
    # 使用 RPC 搜尋隨機梗圖
    response = supabase.rpc('search_meme_by_text', {
        'search_text': user_text
    }).execute()
    
    # 取得結果
    if response.data and len(response.data) > 0:
        meme = response.data[0]
        image_url = meme['image_url']
    else:
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