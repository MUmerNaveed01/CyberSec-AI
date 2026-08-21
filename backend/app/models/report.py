import enum
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func
from app.db.base import Base, UUIDMixin

class ReportType(str, enum.Enum):
    EXECUTIVE = "EXECUTIVE"
    TECHNICAL = "TECHNICAL"
    FULL = "FULL"

class Report(Base, UUIDMixin):
    __tablename__ = "reports"
    
    project_id: Mapped[uuid.UUID]
    scan_id: Mapped[uuid.UUID | None]
    report_type: Mapped[ReportType]
    file_path: Mapped[str | None]
    generated_by: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
