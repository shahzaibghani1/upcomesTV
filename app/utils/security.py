from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from ..config import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# A separate context for refresh token hashing, so it can be changed independently.
# It's good practice to keep them separate to prevent cross-vulnerability.
refresh_token_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Password verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# New: Hash the refresh token
def hash_refresh_token(token: str) -> str:
    return refresh_token_context.hash(token)

# New: Verify the refresh token
def verify_refresh_token(plain_token: str, hashed_token: str) -> bool:
    return refresh_token_context.verify(plain_token, hashed_token)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def create_email_verification_token(user_id: str, expires_minutes: int = 60) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc).timestamp()}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_email_verification_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def create_password_reset_token(user_id: str, expires_minutes: int = 60) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc).timestamp(), "typ": "pwd_reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_password_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "pwd_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None