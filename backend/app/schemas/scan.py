from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.scan import ScanType, ScanStatus

class ScanCreate(BaseModel):
    project_id: UUID
    asset_id: UUID
    scan_type: ScanType

class ScanResponse(BaseModel):
    id: UUID
    project_id: UUID
    asset_id: UUID
    scan_type: ScanType
    status: ScanStatus
    progress: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int
    page: int
    page_size: int
    pages: int
