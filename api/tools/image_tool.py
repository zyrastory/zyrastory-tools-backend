from fastapi import FastAPI, UploadFile, File, Form, APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
#from app import schemas
from schemas.user import UserRequest, UserResponse
from schemas.img import FileRatio, ImgResponse

from PIL import Image
from io import BytesIO
import zipfile
import os

import time, uuid
import mimetypes

router = APIRouter()
TMP_DIR = 'tmp'


'''
API: POST /upload
功能說明: 傳入圖檔(最多N張)，並依照所選格式與品質轉檔或壓縮
參數:
    format_type (str): 目標格式，支援 'jpeg', 'png', 'webp' 等，或 'keep' 保留原始格式
    quality_value (int): 圖片品質 (1-100)
    files (List[UploadFile]): 上傳的圖片檔案列表
回傳: ImgResponse - 包含處理結果、下載連結與壓縮比例資訊
備註: 20250921 新增keep參數，保留原始檔案格式 僅壓縮
'''
@router.post("/upload")
async def upload(
    #預設用前面的參數名稱，假如要不同的話要用alias別名
    #query string 的話 quality: int = Query(...), 
    format_type: str = Form(...),
    quality_value: int = Form(...),
    files: List[UploadFile] = File(..., alias="upload_files")
):
    tmp_uuid = get_uuid()    #本次執行的uuid
    ratios = []
    download_url = f"download/{tmp_uuid}"
    download_all_url = f"downloadAll/{tmp_uuid}"

    folder_path = os.path.join(TMP_DIR, tmp_uuid)
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        content_bytes = await file.read()     # 讀取完整二進位內容
        org_size = len(content_bytes)

        tmp_bytes = BytesIO()
        with Image.open(BytesIO(content_bytes)) as img:
            if format_type=='jpeg':
                img = img.convert("RGB") 
            
            if format_type=='keep':
                img.save(tmp_bytes, img.format.lower(), quality=quality_value, optimize=True)
            else:
                img.save(tmp_bytes, format_type, quality=quality_value, optimize=True)

        tmp_bytes.seek(0)
        new_size = len(tmp_bytes.getvalue())
        ratio = round((new_size / org_size) * 100, 2)

        if format_type=='keep':
            save_name = file.filename
        else:
            save_name = file.filename.rsplit(".", 1)[0] + "." + format_type
        save_path = os.path.join(folder_path, save_name)
        with open(save_path, "wb") as f:
            f.write(tmp_bytes.read())

        org_size_str = format_file_size(org_size)
        new_size_str = format_file_size(new_size)

        ratios.append(FileRatio(filename=save_name, org_size_str=org_size_str, new_size_str=new_size_str, ratio=ratio))
    
    return ImgResponse(
        memo="轉檔完成",
        download_url=download_url,
        download_all_url = download_all_url,
        ratios=ratios,
        quality_value=quality_value
    )


'''
API: GET /download/{uuid}/{filename}
功能說明: 下載單一處理過的圖片檔案
參數:
    uuid (str): 處理任務的唯一識別碼
    filename (str): 要下載的檔案名稱
回傳: FileResponse - 圖片檔案
'''
@router.get("/download/{uuid}/{filename}")
def download(uuid: str, filename: str):

    file_path = os.path.join(TMP_DIR, uuid, filename)

    #要是不存在
    if not os.path.exists(file_path):
        raise SystemError
    
    # 依附檔名判斷
    mime_type, _ = mimetypes.guess_type(file_path) 
    
    return FileResponse(file_path, media_type=mime_type, filename=filename)

'''
API: GET /downloadAll/{uuid}
功能說明: 將該 uuid 的所有處理過的檔案打包成 ZIP 下載
參數:
    uuid (str): 處理任務的唯一識別碼
回傳: StreamingResponse - ZIP 壓縮檔
'''
@router.get("/downloadAll/{uuid}")
def download_all(uuid: str):

    folder_path = os.path.join(TMP_DIR, uuid)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise SystemError

    zip_bytes = BytesIO()
    with zipfile.ZipFile(zip_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)  #不加這個會有一堆路徑??

                #uuid_path = os.path.basename(folder_path)  # 取出 uuid 這一層
                #arcname = os.path.join(uuid_path, os.path.basename(file_path))
                zipf.write(file_path, arcname=arcname)

    zip_bytes.seek(0)  # 回到檔案起始點
    return StreamingResponse(
        zip_bytes,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={uuid}.zip"}
    )




#region API基礎範例 get/post
'''
no: int = Query(..., description="使用者編號")  一般取query string方式
Depends()  >> 把 UserRequest 當 callable 呼叫，並自動從 query string 填值
post 不需要 會自動解析
'''

'''
API: GET /example
功能說明: 範例 GET 端點（示範用）
參數:
    user (UserRequest): 透過 Query String 傳入的使用者資訊
回傳: UserResponse - 使用者回應資料
'''
@router.get("/example", response_model=UserResponse)
def example(user: UserRequest = Depends()):
    
    print("in")
    return UserResponse(
        no=user.no,
        name=user.name,
        memo="備註範例"
    )

'''
API: POST /post_example
功能說明: 範例 POST 端點（示範用）
參數:
    user (UserRequest): 透過 Request Body 傳入的使用者資訊
回傳: UserResponse - 使用者回應資料
'''
@router.post("/post_example", response_model=UserResponse)
def example_post(user: UserRequest):
    
    print("post")
    return UserResponse(
        no=user.no,
        name=user.name,
        memo="備註範例_post"
    )
#endregion


#region 工具
def get_uuid():
    ts= int(time.time())
    rand = uuid.uuid4().hex[:8]
    return f"{ts}{rand}"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:  # 小於 1MB → 顯示 KB
        size_kb = size_bytes / 1024
        return f"{size_kb:.2f} KB"
    else:  # 大於等於 1MB → 顯示 MB
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"


#endregion