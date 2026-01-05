from pydantic import BaseModel,ConfigDict

class UserBase(BaseModel):
    name: str
    no: int

class UserRequest(UserBase):
    pass  

#開放給create?  只是example
class UserCreate(UserBase):
    pass  

class UserResponse(UserBase):
    memo: str