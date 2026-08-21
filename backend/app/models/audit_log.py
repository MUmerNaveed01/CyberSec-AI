import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func, JSON
from app.db.base import Base, UUIDMixin

class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"
    
    user_id: Mapped[uuid.UUID | None]
    action: Mapped[str]
    resource_type: Mapped[str | None]
    resource_id: Mapped[str | None]
    metadata_: Mapped[dict | None] = mapped_column(type_=JSON)
    ip_address: Mapped[str | None]
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
