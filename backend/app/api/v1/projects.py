from datetime import date
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DB, LeadOrAdmin, PentesterOrAbove
from app.models.project import Project
from app.models.user import ProjectMember, User
from app.schemas.project import (
    MemberAdd, MemberResponse, ProjectCreate, ProjectResponse, ProjectUpdate,
)

router = APIRouter()


def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(p.id),
        name=p.name,
        client_name=p.client_name,
        description=p.description,
        status=p.status,
        start_date=p.start_date.isoformat() if p.start_date else None,
        end_date=p.end_date.isoformat() if p.end_date else None,
        created_by=str(p.created_by) if p.created_by else None,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: DB, current_user: CurrentUser):
    if current_user.role == "admin":
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    else:
        result = await db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == current_user.id)
            .order_by(Project.created_at.desc())
        )
    projects = result.scalars().all()
    return [_project_to_response(p) for p in projects]


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, db: DB, current_user: LeadOrAdmin):
    project = Project(
        name=data.name,
        client_name=data.client_name,
        description=data.description,
        start_date=date.fromisoformat(data.start_date) if data.start_date else None,
        end_date=date.fromisoformat(data.end_date) if data.end_date else None,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()

    # Auto-add creator as lead
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="lead",
    )
    db.add(member)
    await db.flush()

    return _project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, data: ProjectUpdate, db: DB, current_user: LeadOrAdmin
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        project.name = data.name
    if data.client_name is not None:
        project.client_name = data.client_name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status
    if data.start_date is not None:
        project.start_date = date.fromisoformat(data.start_date)
    if data.end_date is not None:
        project.end_date = date.fromisoformat(data.end_date)

    await db.flush()
    return _project_to_response(project)


@router.delete("/{project_id}")
async def archive_project(project_id: str, db: DB, current_user: LeadOrAdmin):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = "archived"
    await db.flush()
    return {"detail": "Project archived"}


# --- Member Management ---

@router.get("/{project_id}/members", response_model=list[MemberResponse])
async def list_members(project_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
    )
    members = result.scalars().all()
    return [
        MemberResponse(
            id=str(m.id),
            user_id=str(m.user_id),
            user_email=m.user.email,
            user_name=m.user.full_name,
            role=m.role,
            joined_at=m.joined_at.isoformat(),
        )
        for m in members
    ]


@router.post("/{project_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    project_id: str, data: MemberAdd, db: DB, current_user: LeadOrAdmin
):
    # Check project exists
    proj = await db.execute(select(Project).where(Project.id == project_id))
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Check user exists
    user_result = await db.execute(select(User).where(User.id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already member
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)
    await db.flush()

    return MemberResponse(
        id=str(member.id),
        user_id=str(member.user_id),
        user_email=user.email,
        user_name=user.full_name,
        role=member.role,
        joined_at=member.joined_at.isoformat(),
    )


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: str, user_id: str, db: DB, current_user: LeadOrAdmin
):
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.flush()
    return {"detail": "Member removed"}
