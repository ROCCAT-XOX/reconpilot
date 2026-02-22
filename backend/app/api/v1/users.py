from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.api.deps import AdminUser, CurrentUser, DB, Pagination, PaginatedResponse
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(db: DB, admin: AdminUser, pagination: Pagination):
    # Count total
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar()

    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    users = result.scalars().all()
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


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
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: CurrentUser):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(data: UserUpdate, db: DB, current_user: CurrentUser):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    await db.flush()
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: DB, admin: AdminUser):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


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
    return UserResponse.model_validate(user)


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
