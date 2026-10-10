from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends ,Header , HTTPException
from datetime import datetime, timedelta, timezone


import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM =  os.getenv("ALGORITHM")

def password_hash(password:str ):
    pwd = PasswordHash([Argon2Hasher()])

    hash =  pwd.hash(password)
    return hash

def verify_hash(password:str , hash: str ):
    pwd = PasswordHash([Argon2Hasher()])

    return pwd.verify(password , hash)


def create_access_token(user_id: int , username:str ):
    payload = {
        "sub": str(user_id),
        "user_name":username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
