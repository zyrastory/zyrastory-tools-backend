# base response
from pydantic import BaseModel
from typing import Optional, Any

class ApiResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None
