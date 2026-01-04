# base response
from pydantic import BaseModel,PlainSerializer
from typing import Optional, Any
from typing_extensions import Annotated

class ApiResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None



#在python中是int 轉成json至前端會是千分位的str
CommaInt = Annotated[
    int, 
    PlainSerializer(lambda x: f"{x:,}", return_type=str)
]