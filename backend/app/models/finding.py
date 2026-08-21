import enum
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON
from app.db.base import Base, UUIDMixin, TimestampMixin

class FindingSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class FindingStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    FALSE_POSITIVE = "FALSE_POSITIVE"

class FindingCategory(str, enum.Enum):
    CONFIGURATION = "CONFIGURATION"
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    INJECTION = "INJECTION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    SENSITIVE_DATA = "SENSITIVE_DATA"
    DEPENDENCY = "DEPENDENCY"
    SECRETS = "SECRETS"
    NETWORK = "NETWORK"
    OTHER = "OTHER"

class Finding(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "findings"
    
    scan_id: Mapped[uuid.UUID]
    asset_id: Mapped[uuid.UUID]
    title: Mapped[str]
    description: Mapped[str]
    category: Mapped[FindingCategory]
    severity: Mapped[FindingSeverity]
    confidence: Mapped[float]
    evidence: Mapped[dict] = mapped_column(type_=JSON)
    remediation: Mapped[str]
    cwe: Mapped[str | None]
    cve: Mapped[str | None]
    status: Mapped[FindingStatus] = mapped_column(default=FindingStatus.OPEN)
    risk_score: Mapped[float]
    first_seen_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
