from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()


def _user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=str(u.id),
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at.isoformat(),
        updated_at=u.updated_at.isoformat(),
    )


@router.get("/", response_model=list[UserResponse])
async def list_users(db: DB, admin: AdminUser):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [_user_to_response(u) for u in users]


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
    return _user_to_response(user)


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: CurrentUser):
    return _user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(data: UserUpdate, db: DB, current_user: CurrentUser):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    # Users cannot change their own role or active status
    await db.flush()
    return _user_to_response(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: DB, admin: AdminUser):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, data: UserUpdate, db: DB, admin: AdminUser):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.flush()
    return _user_to_response(user)


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: DB, admin: AdminUser):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user.is_active = False
    await db.flush()
    return {"detail": "User deactivated"}
