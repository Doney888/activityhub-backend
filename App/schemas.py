from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List

# AUTH
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    role: str
    # Поля для фронта, чтобы понимать, нужна ли 2FA
    require_2fa: bool = False
    message: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    avatar_url: Optional[str] = None
    is_verified: bool
    is_2fa_enabled: bool
    
    class Config:
        from_attributes = True

# ACTIVITY
class ActivityResponse(BaseModel):
    id: int
    title: str
    description: str
    category_id: int
    cost_type: str
    mood_type: str
    time_of_day: str
    image_url: Optional[str] = None
    is_sponsored: bool = False
    
    class Config:
        from_attributes = True