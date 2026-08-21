from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.finding import FindingSeverity, FindingStatus, FindingCategory

class FindingUpdate(BaseModel):
    status: FindingStatus | None = None

class FindingResponse(BaseModel):
    id: UUID
    scan_id: UUID
    asset_id: UUID
    title: str
    description: str
    category: FindingCategory
    severity: FindingSeverity
    confidence: float
    evidence: dict
    remediation: str
    cwe: str | None = None
    cve: str | None = None
    status: FindingStatus
    risk_score: float
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}

class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int
    page: int
    page_size: int
    pages: int
