from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DB, CurrentUser, PentesterOrAbove
from app.models.project import Project
from app.models.scope import ScopeTarget
from app.services.scope_validator import build_scope_validator

router = APIRouter()


class ScopeTargetCreate(BaseModel):
    target_type: str = Field(..., pattern="^(domain|ip|ip_range|url)$")
    target_value: str = Field(..., max_length=500)
    is_excluded: bool = False
    notes: str | None = None


class ScopeTargetResponse(BaseModel):
    id: str
    project_id: str
    target_type: str
    target_value: str
    is_excluded: bool
    notes: str | None
    added_by: str | None
    created_at: str


class ScopeValidateRequest(BaseModel):
    targets: list[str]


class ScopeValidateResponse(BaseModel):
    results: dict[str, dict]  # target -> {is_valid, reason}


def _scope_to_response(st: ScopeTarget) -> ScopeTargetResponse:
    return ScopeTargetResponse(
        id=str(st.id),
        project_id=str(st.project_id),
        target_type=st.target_type,
        target_value=st.target_value,
        is_excluded=st.is_excluded,
        notes=st.notes,
        added_by=str(st.added_by) if st.added_by else None,
        created_at=st.created_at.isoformat(),
    )


@router.get(
    "/{project_id}/scope",
    response_model=list[ScopeTargetResponse],
)
async def list_scope_targets(
    project_id: str, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(ScopeTarget)
        .where(ScopeTarget.project_id == project_id)
        .order_by(ScopeTarget.created_at)
    )
    targets = result.scalars().all()
    return [_scope_to_response(st) for st in targets]


@router.post(
    "/{project_id}/scope",
    response_model=ScopeTargetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_scope_target(
    project_id: str,
    data: ScopeTargetCreate,
    db: DB,
    current_user: PentesterOrAbove,
):
    # Verify project exists
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for duplicates
    existing = await db.execute(
        select(ScopeTarget).where(
            ScopeTarget.project_id == project_id,
            ScopeTarget.target_value == data.target_value,
            ScopeTarget.is_excluded == data.is_excluded,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Scope target already exists")

    target = ScopeTarget(
        project_id=project_id,
        target_type=data.target_type,
        target_value=data.target_value,
        is_excluded=data.is_excluded,
        notes=data.notes,
        added_by=current_user.id,
    )
    db.add(target)
    await db.flush()
    return _scope_to_response(target)


@router.delete("/{project_id}/scope/{target_id}")
async def remove_scope_target(
    project_id: str,
    target_id: str,
    db: DB,
    current_user: PentesterOrAbove,
):
    result = await db.execute(
        select(ScopeTarget).where(
            ScopeTarget.id == target_id,
            ScopeTarget.project_id == project_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Scope target not found")
    await db.delete(target)
    await db.flush()
    return {"detail": "Scope target removed"}


@router.post(
    "/{project_id}/scope/validate",
    response_model=ScopeValidateResponse,
)
async def validate_scope(
    project_id: str,
    data: ScopeValidateRequest,
    db: DB,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ScopeTarget).where(ScopeTarget.project_id == project_id)
    )
    scope_targets = result.scalars().all()

    if not scope_targets:
        raise HTTPException(status_code=400, detail="No scope targets defined for this project")

    validator = build_scope_validator(scope_targets)
    results = validator.validate_multiple(data.targets)

    return ScopeValidateResponse(
        results={
            target: {"is_valid": r.is_valid, "reason": r.reason}
            for target, r in results.items()
        }
    )
