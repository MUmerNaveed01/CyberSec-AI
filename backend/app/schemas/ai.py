from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class AIAnalysisRequest(BaseModel):
    pass

class AIAnalysisResponse(BaseModel):
    id: UUID
    finding_id: UUID
    summary: str
    technical_explanation: str
    business_impact: str
    remediation: str
    priority: str
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}
