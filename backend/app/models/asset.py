import enum
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin

class AssetType(str, enum.Enum):
    WEBSITE = "WEBSITE"
    SOURCE_CODE = "SOURCE_CODE"
    DEPENDENCY_MANIFEST = "DEPENDENCY_MANIFEST"

class AssetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"

class Asset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assets"
    
    project_id: Mapped[uuid.UUID]
    name: Mapped[str]
    type: Mapped[AssetType]
    target: Mapped[str]
    description: Mapped[str | None]
    authorization_confirmed: Mapped[bool] = mapped_column(default=False)
    status: Mapped[AssetStatus] = mapped_column(default=AssetStatus.ACTIVE)
