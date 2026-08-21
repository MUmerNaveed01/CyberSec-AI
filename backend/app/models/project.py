import enum
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin

class ProjectStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"

class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"
    
    name: Mapped[str]
    description: Mapped[str | None]
    owner_id: Mapped[uuid.UUID]
    status: Mapped[ProjectStatus] = mapped_column(default=ProjectStatus.ACTIVE)
