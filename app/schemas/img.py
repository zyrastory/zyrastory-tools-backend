from pydantic import BaseModel,ConfigDict
from typing import List

class imgBase(BaseModel):
    pass

class fileRatio(BaseModel):
    filename: str
    org_size_str: str
    new_size_str: str
    ratio: float

class imgResponse(imgBase):
    memo: str
    download_url: str
    ratios: List[fileRatio]


#class Config:
    #orm_mode = True  # 讓 SQLAlchemy model 可以轉換成 Pydantic schema
    #model_config = ConfigDict(from_attributes=True) #新版寫法，功能一樣，負責處理映射

