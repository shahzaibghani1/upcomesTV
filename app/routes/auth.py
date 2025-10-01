from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from ..models.user import User, UserCreate, UserLogin, UserOut
from ..utils.security import (
    hash_password,
    verify_password,
    create_email_verification_token,
    decode_email_verification_token,
    decode_token,
    hash_refresh_token,
    verify_refresh_token,
)
from ..utils.email import send_email, verify_email_existence
from ..config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    ALGORITHM,
)
from datetime import datetime, timedelta, timezone
import uuid
from pydantic import BaseModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------------- HELPER ---------------- #
def create_token(user: User, expires_delta: timedelta) -> str:
    pwd_changed_at_ts = int(user.password_changed_at.timestamp()) if user.password_changed_at else 0
    to_encode = {
        "sub": str(user.id),
        "pwd_changed_at": pwd_changed_at_ts,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + expires_delta).timestamp())
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- GET CURRENT USER ---------------- #
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    if payload is None:
        print("Token decode failed")
        raise HTTPException(status_code=401, detail="Token invalid or expired")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_pwd_changed_at = payload.get("pwd_changed_at", 0)
    user_pwd_changed_at = int(user.password_changed_at.timestamp()) if user.password_changed_at else 0

    # Only invalidate if password was actually changed AFTER token issue
    if user_pwd_changed_at > 0 and token_pwd_changed_at < user_pwd_changed_at:
        raise HTTPException(status_code=401, detail="Token invalid due to password change")

    return user


# ---------------- REFRESH TOKEN BODY MODEL ---------------- #
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ---------------- AUTH ROUTES ---------------- #
@router.post("/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    email_check = await verify_email_existence(user.email)
    if not email_check["is_valid"]:
        raise HTTPException(status_code=400, detail=f"Invalid email: {email_check['details']}")
    
    if await User.find_one(User.email == user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pw,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        password_changed_at=datetime.now(timezone.utc),
        is_verified=False,
        is_subscribed=False
    )
    await new_user.insert()

    token = create_email_verification_token(str(new_user.id))
    verification_link = f"http://localhost:8000/auth/verify-email?token={token}"

    background_tasks.add_task(
        send_email,
        to_email=new_user.email,
        subject="Verify your email",
        body=f"Click this link to verify your email: {verification_link}"
    )

    return {"msg": "User registered successfully, please verify your email."}

@router.post("/login")
async def login(user: UserLogin):
    existing_user = await User.find_one(User.email == user.email)
    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not existing_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_token(existing_user, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token_plain = str(uuid.uuid4())
    hashed_refresh_token = hash_refresh_token(refresh_token_plain)

    existing_user.hashed_refresh_token = hashed_refresh_token
    existing_user.refresh_token_expiry = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await existing_user.save()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_plain,
        "token_type": "bearer",
        "user": {
            "id": str(existing_user.id),
            "name": existing_user.name,
            "email": existing_user.email,
            "is_subscribed": existing_user.is_subscribed
        }
    }

@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest):
    users = await User.find_all().to_list()
    user = None
    for u in users:
        if u.hashed_refresh_token and verify_refresh_token(payload.refresh_token, u.hashed_refresh_token):
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Fix timezone-aware vs naive datetime
    expiry = user.refresh_token_expiry
    if not expiry:
        raise HTTPException(status_code=401, detail="Invalid refresh token (no expiry set)")

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Expired refresh token")

    # Issue new refresh + access tokens
    new_refresh_token_plain = str(uuid.uuid4())
    new_hashed_refresh_token = hash_refresh_token(new_refresh_token_plain)
    user.hashed_refresh_token = new_hashed_refresh_token
    user.refresh_token_expiry = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await user.save()

    new_access_token = create_token(user, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_plain,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        is_subscribed=current_user.is_subscribed
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Invalidate refresh tokens
    current_user.hashed_refresh_token = None
    current_user.refresh_token_expiry = None
    await current_user.save()

    return {"msg": "Logout success"}

@router.get("/verify-email")
async def verify_email(token: str):
    try:
        user_id = decode_email_verification_token(token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"msg": "Account already verified. Please log in."}

    user.is_verified = True
    await user.save()
    return {"msg": "Email verified successfully! You can now log in."}
