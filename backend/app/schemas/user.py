from pydantic import BaseModel, Field


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
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Support ORM objects by converting UUID/datetime fields."""
        if hasattr(obj, "__table__"):
            data = {
                "id": str(obj.id),
                "email": obj.email,
                "full_name": obj.full_name,
                "role": obj.role,
                "is_active": obj.is_active,
                "created_at": obj.created_at.isoformat() if obj.created_at else "",
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
