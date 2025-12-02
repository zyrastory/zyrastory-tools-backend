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
    ReplyMessageRequest, ImageMessage, TextMessage,
    QuickReply, QuickReplyItem, MessageAction
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

# 特殊映射
TAG_ALIASES = {
    "5/454": "政治",
    "mygo": "MyGO",
    "mygO": "MyGO",
    "myGO": "MyGO",
    "MYGO": "MyGO"
}

# 指令
COMMANDS = {"/random","/help"}

#KEYWORDS = {"股票", "政治", "周星馳"}

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
    user_text = event.message.text
    
    #20251103 新增指令判斷
    if user_text in COMMANDS:
        handle_command(event, user_text)
        return

    supabase = database.supabase
    redis_client = database.get_redis()
    redis_tags = database.get_redis_tags()  #20251202 修正tags無正常更新，於datebase引入時就暫存reference了?
    
    image_url = None
    response = None

    logger.info(redis_tags)


    if user_text in TAG_ALIASES:
        user_text = TAG_ALIASES[user_text]

    #20251026 新增關鍵字 redis 判斷 20251102 移除寫死關鍵字判斷
    if user_text in redis_tags:
        cache_key = f"tag:{user_text}"
        if redis_client.exists(cache_key):
            image_url = redis_client.srandmember(cache_key)
            logger.info(f'成功從redis取值-{user_text}')
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

'''
針對 /指令的回覆
'''
def handle_command(event, user_text):
    supabase = database.supabase
    redis_client = database.get_redis()
    redis_tags = database.get_redis_tags()  #20251202 修正tags無正常更新
    image_url = None
    response = None

    if user_text == "/random":
        if redis_tags:
            randomTag = random.choice(list(redis_tags))
            cache_key = f"tag:{randomTag}"
            if redis_client.exists(cache_key):
                image_url = redis_client.srandmember(cache_key)
            else: #不太該發生，redis tag 有值 代表 redis就應該有值
                response = supabase.rpc(
                    'search_meme_by_tag',
                    {'search_tag': randomTag}
                ).execute()
                logger.info('random tag 依然走 rpc')

        else: #這其實也不該發生
            response = supabase.rpc(
                'search_meme_by_tag',
                {'search_tag': 'MyGO'}
            ).execute()
            logger.info('random redis_tags 不存在')
        if response is not None:
            if response.data and len(response.data) > 0:
                image_url = response.data[0]['image_url']
        
        #最不該發生的情況
        if image_url is None:  
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
    #20251105 測試quick reply
    elif user_text == "/help":
        logger.info('command-help')
        quick_reply = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="隨機", text="/random")),
            QuickReplyItem(action=MessageAction(label="周星馳", text="周星馳")),
            QuickReplyItem(action=MessageAction(label="玫瑰瞳鈴眼", text="玫瑰瞳鈴眼")),
            QuickReplyItem(action=MessageAction(label="海綿寶寶", text="海綿寶寶")),
            QuickReplyItem(action=MessageAction(label="MyGO", text="MyGo")),
            QuickReplyItem(action=MessageAction(label="政治", text="政治")),
        ])

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="不知道該怎麼選嗎? 以下是常見關鍵字供點選",
                            quick_reply=quick_reply
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