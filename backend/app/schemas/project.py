from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    client_name: str = Field(..., max_length=255)
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|completed|archived)$")
    start_date: str | None = None
    end_date: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    client_name: str
    description: str | None
    status: str
    start_date: str | None
    end_date: str | None
    created_by: str | None
    created_at: str
    updated_at: str


class MemberAdd(BaseModel):
    user_id: str
    role: str = Field(default="pentester", pattern="^(lead|pentester|viewer)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    role: str
    joined_at: str
