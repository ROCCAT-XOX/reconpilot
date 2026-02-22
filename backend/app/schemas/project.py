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
    model_config = {"from_attributes": True}

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

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, "__table__"):
            data = {
                "id": str(obj.id),
                "name": obj.name,
                "client_name": obj.client_name,
                "description": obj.description,
                "status": obj.status,
                "start_date": obj.start_date.isoformat() if obj.start_date else None,
                "end_date": obj.end_date.isoformat() if obj.end_date else None,
                "created_by": str(obj.created_by) if obj.created_by else None,
                "created_at": obj.created_at.isoformat() if obj.created_at else "",
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


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
