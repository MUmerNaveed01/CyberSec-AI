from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.project import ProjectStatus

class ProjectStats(BaseModel):
    security_score: int = 100
    assets_count: int = 0
    scans_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: ProjectStatus | None = None

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    stats: ProjectStats | None = None

    model_config = {"from_attributes": True}

class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
