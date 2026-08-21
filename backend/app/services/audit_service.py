from datetime import datetime, timezone
from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_log)
        try:
            await db.flush()
            logger.info("Audit log recorded", action=action, user_id=str(user_id) if user_id else None)
        except Exception as e:
            logger.error("Failed to write audit log", error=str(e), action=action)
        return audit_log
