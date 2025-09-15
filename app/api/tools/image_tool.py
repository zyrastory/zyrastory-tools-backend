from fastapi import FastAPI, UploadFile, File, Form, APIRouter, Depends
from fastapi.responses import FileResponse
from typing import List
#from app import schemas
from app.schemas.user import userRequest, userResponse
from app.schemas.img import fileRatio, imgResponse

from PIL import Image
from io import BytesIO
#import zipfile
import os

import time, uuid

router = APIRouter()
TMP_DIR = 'tmp'


'''
API: /upload
功能說明: 傳入圖檔(最多N張)，並依照所選比例轉檔(webp?)， 預計回傳zip用以降低transfer (看一張圖要不要直接回傳webp TODO)
'''
@router.post("/upload")
async def upload(
    #預設用前面的參數名稱，假如要不同的話要用alias別名
    #query string 的話 quality: int = Query(...), 
    quality_value: int = Form(...),
    files: List[UploadFile] = File(..., alias="upload_files")
):
    tmpUUID = get_uuid()    #本次執行的uuid
    ratios = []
    download_url = f"download/{tmpUUID}"

    folder_path = os.path.join(TMP_DIR, tmpUUID)
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        content_bytes = await file.read()     # 讀取完整二進位內容
        org_size = len(content_bytes)

        tmp_bytes = BytesIO()
        with Image.open(BytesIO(content_bytes)) as img:
            img.save(tmp_bytes, "webp", quality=quality_value, optimize=True)

        tmp_bytes.seek(0)
        new_size = len(tmp_bytes.getvalue())
        ratio = round((new_size / org_size) * 100, 2)

        save_name = file.filename.rsplit(".", 1)[0] + ".webp"
        save_path = os.path.join(folder_path, save_name)
        with open(save_path, "wb") as f:
            f.write(tmp_bytes.read())

        org_size_str = format_file_size(org_size)
        new_size_str = format_file_size(new_size)

        ratios.append(fileRatio(filename=save_name, org_size_str=org_size_str,new_size_str=new_size_str, ratio=ratio))

    #直接寫入zip??
    '''
    zip_bytes = BytesIO()
    with zipfile.ZipFile(zip_bytes,'w') as zip:
        for file in files:
            print(file.filename)       # 原始檔名
            print(file.content_type)   # MIME 類型，例如 image/jpeg


            tmp_bytes = BytesIO()   #暫存
            content_bytes = await file.read()  # 讀取完整二進位內容
            org_size = len(content_bytes)

            with Image.open(BytesIO(content_bytes)) as img:
                img.save(tmp_bytes, 'webp', quality=quality_value, optimize=True)

                tmp_bytes.seek(0)
                new_size = len(tmp_bytes.getvalue())
                ratio = new_size/org_size

                tmp_name = file.filename.rsplit(".",1)[0]+'.webp'
                zip.writestr(tmp_name, tmp_bytes.read())

        zip_bytes.seek(0)
    '''
        
    
    return imgResponse(
        memo="轉檔完成",
        download_url=download_url,
        ratios=ratios,
        quality_value=quality_value
    )


@router.get("/download/{uuid}/{filename}")
def download(uuid: str, filename: str):

    file_path = os.path.join(TMP_DIR, uuid, filename)

    #要是不存在
    if not os.path.exists(file_path):
        raise SystemError
    
    return FileResponse(file_path, media_type="image/webp", filename=filename)





#region API基礎範例 get/post
'''
no: int = Query(..., description="使用者編號")  一般取query string方式
Depends()  >> 把 userRequest 當 callable 呼叫，並自動從 query string 填值
post 不需要 會自動解析
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
def get_uuid():
    ts= int(time.time())
    rand = uuid.uuid4().hex[:6]
    return f"{ts}{rand}"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:  # 小於 1MB → 顯示 KB
        size_kb = size_bytes / 1024
        return f"{size_kb:.2f} KB"
    else:  # 大於等於 1MB → 顯示 MB
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"


#endregion