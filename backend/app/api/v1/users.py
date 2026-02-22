from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.core.security import hash_password
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "pentester"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool


@router.get("/", response_model=list[UserResponse])
async def list_users(db: DB, admin: AdminUser):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserResponse(
            id=str(u.id), email=u.email, full_name=u.full_name,
            role=u.role, is_active=u.is_active,
        )
        for u in users
    ]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: DB, admin: AdminUser):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    return UserResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        role=user.role, is_active=user.is_active,
    )


@router.get("/me")
async def get_profile(current_user: CurrentUser):
    return UserResponse(
        id=str(current_user.id), email=current_user.email,
        full_name=current_user.full_name, role=current_user.role,
        is_active=current_user.is_active,
    )
