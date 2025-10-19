import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
SECRET_KEY=os.getenv('SECRET_KEY','change_me')
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES','120'))

# Use a robust, pure-Python default (pbkdf2_sha256) to avoid platform-specific native deps.
# We intentionally do NOT include bcrypt here to prevent runtime/import errors in slim images.
pwd=CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')

def hash_password(p: str) -> str:
    """Hash a password using pbkdf2_sha256 (pure Python, portable)."""
    # Basic type validation to avoid confusing errors downstream
    if not isinstance(p, str) or not p:
        raise ValueError("password must be a non-empty string")
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)
def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
