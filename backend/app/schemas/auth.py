from typing import Optional, Any

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: Optional[str] = None
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    session_id: Optional[str] = None
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    user: Optional[Any]
    access_token: str
    refresh_token: str
    session_id: Optional[str] = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
    device_name: Optional[str] = None
    device_info: Optional[str] = None


class UserSessionResponse(BaseModel):
    id: str
    device_name: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str
    last_seen_at: str
    expires_at: str
    is_current: bool = False


class LogoutAllRequest(BaseModel):
    keep_current: bool = True


class CreateClientRequest(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    password: str
    # Optional client profile fields set at creation
    status: Optional[str] = None
    goals: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
