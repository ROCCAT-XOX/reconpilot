from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=12)
    full_name: str = Field(..., max_length=255)
    role: str = Field(default="pentester", pattern="^(admin|lead|pentester|viewer)$")


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = Field(default=None, pattern="^(admin|lead|pentester|viewer)$")
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
