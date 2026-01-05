'''
後台操作用
'''

from datetime import datetime, timedelta, timezone
from fastapi import  APIRouter, FastAPI, Request, HTTPException, Header, Depends, Response
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from schemas.base import ApiResponse
from schemas.login import LoginRequest
from schemas.dashboard import DashboardResponse, RedisTagCount
from schemas.memes import MemeUpdateRequest, MemeSearchRequest, MemeResponse, MemeSearchResponse
import os

from dotenv import load_dotenv
from core import database
from core.security import create_token, verify_token_from_request, hash_password,verify_password


import logging

logger = logging.getLogger(__name__)

load_dotenv() 

#router = APIRouter()
login_router = APIRouter(prefix="/admin")
admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(verify_token_from_request)]
)


# region 登入相關
'''
API: POST /admin/login
功能說明: 管理員登入，驗證帳號密碼後回傳 JWT Token
參數:
    login_data (LoginRequest): 登入資訊，包含 username 和 password
    login_response (Response): FastAPI Response 物件，用於設定 Cookie
回傳: dict - {"ok": True}，JWT Token 會設定在 Cookie 中
'''
@login_router.post("/login")
def admin_login(login_data: LoginRequest, login_response: Response):
    supabase = database.supabase

    #hashed_str = hash_password(login_data.password)

    response = supabase.rpc('get_admin_by_username', {
        'login_name': login_data.username
    }).execute()

    result = False

    # 取得結果
    if response is not None:
        if response.data and len(response.data) > 0:
            rpc_data = response.data[0]
            hashed_password = rpc_data['hashed_password']
            result = True
        
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 用 verify_password 比對
    if not verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    
    #產生jwt並設定  採token標準定義
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(login_data.username),        # 對象
        "iat": int(now.timestamp()),            # 甚麼時候發行
        "exp": int((now + timedelta(hours=1)).timestamp()),    #到期時間
    }
    jwt = create_token(payload)

    login_response.set_cookie(
        key="zyrastory_token",
        value=jwt,
        httponly=False,  #True: JS讀不到，瀏覽器自動帶
        secure=False,    #https    
        max_age=3800,   #X秒(預估對標jwt expire) 以防閒置或關閉瀏覽器導致丟失
        samesite="lax",
        #path="/api/admin",
        path="/"
    )

    return {"ok": True}

'''
API: GET /admin/me
功能說明: 驗證當前 JWT Token 是否有效
參數:
    user_message: 透過 Depends 自動從 Cookie 取得並驗證的 Token
回傳: Response - HTTP 200 狀態碼
'''
@login_router.get("/me")
async def check_token(user_message = Depends(verify_token_from_request)):
    return Response(status_code=200)

# endregion

# region 取得dashboard資料
'''
API: GET /admin/dashboard
功能說明: 取得管理後台 Dashboard 統計資料
回傳: DashboardResponse - 包含梗圖總數與標籤統計資料
備註: 需要管理員權限（JWT Token）
'''
@admin_router.get("/dashboard")
async def get_dashboard_data():
    redis_client = database.redis_client
    redis_count = redis_client.zrevrange("tag_count", 0, 19, withscores=True)
    formatted_tags = [
        RedisTagCount(
            tag_name = tag, 
            count = int(count)
        )
        for tag, count in redis_count
    ]

    meme_total_count = int(redis_client.get("meme_total_count"))
    response = DashboardResponse(total_count=meme_total_count, tag_counts=formatted_tags)
    return response
# endregion

# region 梗圖管理  嘗試走Restful風格

'''
API: GET /admin/memes
功能說明: 依條件搜尋梗圖，支援分頁、關鍵字、標籤、狀態篩選
參數:
    condition (MemeSearchRequest): 透過 Query String 傳入的搜尋條件
        - page (int): 頁碼，從 1 開始
        - page_size (int): 每頁筆數，範圍 1-200
        - content (str, optional): 內容關鍵字搜尋
        - tags (str, optional): 標籤篩選
        - is_active (str, optional): 啟用狀態篩選 ('1' 或 '0')
回傳: MemeSearchResponse - 包含梗圖列表、總數、分頁資訊
備註: 需要管理員權限（JWT Token）
'''
@admin_router.get("/memes")
async def search_memes_by_condition(condition: MemeSearchRequest = Depends()):
    supabase = database.supabase

    start = (condition.page - 1) * condition.page_size          # 從 1 開始
    end = start + condition.page_size-1

    #加上count exact會取得總筆數
    query = supabase.table("memes") \
        .select("*", count="exact") \
        .order("id", desc=False)

    #關鍵字、內容
    if condition.content:
        query = query.ilike("content", f"%{condition.content}%")

    #標籤
    if condition.tags:
        query = query.contains("tags", [condition.tags])

    #狀態(啟用/停用)
    if condition.is_active:
        query = query.eq("is_active", condition.is_active == '1')

    # 分頁 + 取得總數
    response = query.range(start, end).execute()

    # 取得資料與總數
    memes = response.data
    total = response.count or 0 

    meme_list = [MemeResponse(**meme) for meme in memes]

    total_pages = (total + condition.page_size - 1) // condition.page_size if total else 0

    return MemeSearchResponse(
        data=meme_list,
        total=total,
        page=condition.page,
        page_size=condition.page_size,
        total_pages=total_pages,
    )

'''
API: PATCH /admin/memes/{meme_id}
功能說明: 更新指定梗圖的內容、標籤或啟用狀態
參數:
    meme_id (str): 梗圖 ID
    request (MemeUpdateRequest): 要更新的欄位
        - content (str, optional): 內容
        - tags (List[str], optional): 標籤列表
        - is_active (bool, optional): 啟用狀態
回傳: None 或 ApiResponse - 更新結果
備註: 需要管理員權限（JWT Token）
'''
@admin_router.patch("/memes/{meme_id}")
async def update_memes(meme_id: str, request: MemeUpdateRequest):
    supabase = database.supabase

    if request.content is None and request.tags is None and request.is_active is None:
        return ApiResponse(status="failed",message="no Data found"),400
    
    try:
        if request.content is not None:
            response = supabase.table("memes") \
            .update({"content": request.content }) \
            .eq("id", meme_id) \
            .execute()
        
        elif request.is_active is not None:
            response = supabase.table("memes") \
            .update({"is_active": request.is_active}) \
            .eq("id", meme_id) \
            .execute()
    except:
        raise HTTPException(status_code=500, detail="Meme update failed")
    return None
# endregion