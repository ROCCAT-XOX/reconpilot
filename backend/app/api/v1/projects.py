from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models.project import Project

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    client_name: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    client_name: str
    description: str | None
    status: str
    created_at: str


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=str(p.id), name=p.name, client_name=p.client_name,
            description=p.description, status=p.status,
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, db: DB, current_user: CurrentUser):
    project = Project(
        name=data.name,
        client_name=data.client_name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()
    return ProjectResponse(
        id=str(project.id), name=project.name, client_name=project.client_name,
        description=project.description, status=project.status,
        created_at=project.created_at.isoformat(),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=str(project.id), name=project.name, client_name=project.client_name,
        description=project.description, status=project.status,
        created_at=project.created_at.isoformat(),
    )
