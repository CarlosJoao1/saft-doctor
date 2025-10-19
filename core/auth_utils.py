import os
from datetime import datetime,timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
SECRET_KEY=os.getenv('SECRET_KEY','change_me')
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES','120'))
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto')
def hash_password(p:str)->str: return pwd.hash(p)
def verify_password(p:str,h:str)->bool: return pwd.verify(p,h)
def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
    to_encode=data.copy(); expire=datetime.utcnow()+(expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp':expire}); return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
