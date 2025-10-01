from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone


class User(Document):
    name: str
    email: EmailStr
    hashed_password: str
    is_verified: bool = False
    is_subscribed: bool = False
    hashed_refresh_token: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_subscribed: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
