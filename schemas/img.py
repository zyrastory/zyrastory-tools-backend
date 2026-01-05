from pydantic import BaseModel,ConfigDict
from typing import List

class ImgBase(BaseModel):
    pass

class FileRatio(BaseModel):
    filename: str
    org_size_str: str
    new_size_str: str
    ratio: float

class ImgResponse(ImgBase):
    memo: str
    download_url: str
    download_all_url: str
    ratios: List[FileRatio]


#class Config:
    #orm_mode = True  # 讓 SQLAlchemy model 可以轉換成 Pydantic schema
    #model_config = ConfigDict(from_attributes=True) #新版寫法，功能一樣，負責處理映射

