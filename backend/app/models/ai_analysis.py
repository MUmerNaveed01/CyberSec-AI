import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func
from app.db.base import Base, UUIDMixin

class AIAnalysis(Base, UUIDMixin):
    __tablename__ = "ai_analyses"
    
    finding_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    summary: Mapped[str]
    technical_explanation: Mapped[str]
    business_impact: Mapped[str]
    remediation: Mapped[str]
    priority: Mapped[str]
    model: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
