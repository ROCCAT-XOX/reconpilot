from fastapi import APIRouter

from app.api.v1 import auth, projects, scans, findings, reports, users, scope
from app.api.v1.scans import project_scans_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scope.router, prefix="/projects", tags=["scope"])
api_router.include_router(project_scans_router, prefix="/projects", tags=["scans"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(findings.router, prefix="/findings", tags=["findings"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
