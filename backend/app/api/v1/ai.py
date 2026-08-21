from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import AIAnalysisResponse
from app.services.ai_service import AIService
from app.api.v1.deps import get_current_active_user, require_analyst

router = APIRouter()

@router.post("/findings/{finding_id}/analyze", response_model=AIAnalysisResponse, summary="Analyze finding with AI Analyst")
async def analyze_finding(
    finding_id: UUID,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    analysis = await AIService.analyze_finding(db, finding_id)
    return AIAnalysisResponse.model_validate(analysis)
