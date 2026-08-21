import enum
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin

class ScanType(str, enum.Enum):
    WEBSITE = "WEBSITE"
    SECRETS = "SECRETS"
    DEPENDENCIES = "DEPENDENCIES"

class ScanStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Scan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scans"
    
    project_id: Mapped[uuid.UUID]
    asset_id: Mapped[uuid.UUID]
    scan_type: Mapped[ScanType]
    status: Mapped[ScanStatus] = mapped_column(default=ScanStatus.QUEUED)
    progress: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    error_message: Mapped[str | None]
    created_by: Mapped[uuid.UUID]
