'''
core.security 的 Docstring
將加密相關獨立出來
'''
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
import redis
import os

from dotenv import load_dotenv
from core.logger import logger


from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  #64MB
    parallelism=1,      #1核
)

ALGORITHM = "HS256"
load_dotenv()  # 讀取 .env  >> 測試環境用
JWT_SECRET = os.getenv("JWT_SECRET")

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        password_hasher.verify(hashed, plain)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False
    
'''
jwt token 加解密相關
'''
def create_token(data: dict):
    payload = data.copy()
    #payload["exp"] = datetime.utcnow() + timedelta(minutes=expire_min)
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def verify_token_from_request(request: Request):
    token = request.cookies.get("zyrastory_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="no token",
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token error",
        )