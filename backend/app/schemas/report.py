from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.report import ReportType

class ReportCreate(BaseModel):
    project_id: UUID
    scan_id: UUID | None = None
    report_type: ReportType

class ReportResponse(BaseModel):
    id: UUID
    project_id: UUID
    scan_id: UUID | None = None
    report_type: ReportType
    file_path: str | None = None
    generated_by: UUID
    created_at: datetime
    content: str | None = None

    model_config = {"from_attributes": True}

class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
    pages: int
