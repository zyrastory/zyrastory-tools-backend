from pydantic import BaseModel,ConfigDict

class userBase(BaseModel):
    name: str
    no: int

class userRequest(userBase):
    pass  

#開放給create?  只是example
class userCreate(userBase):
    pass  

class userResponse(userBase):
    memo: str