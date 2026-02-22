from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import is_token_blacklisted
from app.core.security import (
    InvalidTokenError,
    TokenExpiredError,
    WrongTokenTypeError,
    verify_token,
)
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# RBAC permission matrix
ROLE_PERMISSIONS = {
    "admin": {
        "users.manage", "projects.create", "projects.edit", "projects.delete",
        "team.manage", "scope.define", "scans.manage", "findings.edit",
        "findings.view", "reports.generate", "reports.view", "audit.view",
        "settings.manage",
    },
    "lead": {
        "projects.create", "projects.edit", "team.manage", "scope.define",
        "scans.manage", "findings.edit", "findings.view", "reports.generate",
        "reports.view", "audit.view",
    },
    "pentester": {
        "scope.define", "scans.manage", "findings.edit", "findings.view",
        "reports.generate", "reports.view",
    },
    "viewer": {
        "findings.view", "reports.view",
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        # Check blacklist (fail-open if Redis is down)
        try:
            if await is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Redis down — fail open
        payload = verify_token(token, expected_type="access")
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, WrongTokenTypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(*allowed_roles: str):
    """Dependency factory that checks if user has one of the allowed roles."""
    async def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return _check


def require_permission(permission: str):
    """Dependency factory that checks if user has a specific permission."""
    async def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return current_user
    return _check


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# --- Pagination ---

@dataclass
class PaginationParams:
    page: int
    per_page: int
    offset: int


def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(
        page=page,
        per_page=per_page,
        offset=(page - 1) * per_page,
    )


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int


Pagination = Annotated[PaginationParams, Depends(get_pagination)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]

# Role-based dependencies
LeadOrAdmin = Annotated[User, Depends(require_role("admin", "lead"))]
PentesterOrAbove = Annotated[User, Depends(require_role("admin", "lead", "pentester"))]
AnyAuthenticated = CurrentUser
