# app/utils/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..config import SECRET_KEY, ALGORITHM
import bcrypt

#  Use bcrypt_sha256 to safely support long passwords (pre-hashes before bcrypt)
# pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
# refresh_token_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

# Hash password (always returns str)
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def hash_refresh_token(token: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(token.encode("utf-8"), salt).decode("utf-8")

def verify_refresh_token(plain_token: str, hashed_token: Optional[str]) -> bool:
    try:
        return bcrypt.checkpw(
            plain_token.encode("utf-8"), hashed_token.encode("utf-8")
        )
    except Exception:
        return False

# JWT helpers (use integer timestamps)
def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def create_email_verification_token(user_id: str, expires_minutes: int = 60) -> str:
    expire_ts = _now_ts() + int(expires_minutes * 60)
    payload = {"sub": user_id, "exp": expire_ts, "iat": _now_ts()}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_email_verification_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def create_password_reset_token(user_id: str, expires_minutes: int = 60) -> str:
    expire_ts = _now_ts() + int(expires_minutes * 60)
    payload = {"sub": user_id, "exp": expire_ts, "iat": _now_ts(), "typ": "pwd_reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "pwd_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None
