from pydantic import BaseModel,ConfigDict
from typing import List

class LoginRequest(BaseModel):
    username: str
    password: str


#class Config:
    #orm_mode = True  # 讓 SQLAlchemy model 可以轉換成 Pydantic schema
    #model_config = ConfigDict(from_attributes=True) #新版寫法，功能一樣，負責處理映射

