from uuid import UUID
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.asset import AssetCreate, AssetUpdate
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class AssetService:
    @staticmethod
    def validate_asset_target(asset_type: AssetType, target: str) -> None:
        target = target.strip()
        if asset_type == AssetType.WEBSITE:
            parsed = urlparse(target)
            if not parsed.scheme or parsed.scheme not in ["http", "https"]:
                raise ValidationError("Website target must start with http:// or https://")
            if not parsed.netloc:
                raise ValidationError("Website target must contain a valid domain name or hostname")
            # Prohibit internal and cloud metadata hostnames directly
            blocked_hosts = ["localhost", "127.0.0.1", "::1", "169.254.169.254", "metadata.google.internal"]
            if parsed.netloc.split(":")[0].lower() in blocked_hosts:
                raise ValidationError("Scanning localhost, internal, or cloud metadata endpoints is prohibited")

    @classmethod
    async def get_assets(
        cls,
        db: AsyncSession,
        current_user: User,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Asset], int]:
        query = select(Asset).join(Project, Asset.project_id == Project.id)
        count_query = select(func.count(Asset.id)).join(Project, Asset.project_id == Project.id)

        if project_id:
            query = query.where(Asset.project_id == project_id)
            count_query = count_query.where(Asset.project_id == project_id)

        if current_user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == current_user.id)
            count_query = count_query.where(Project.owner_id == current_user.id)

        query = query.order_by(desc(Asset.created_at)).offset(offset).limit(limit)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        assets_res = await db.execute(query)
        assets = assets_res.scalars().all()

        return list(assets), total

    @classmethod
    async def get_asset_by_id(
        cls,
        db: AsyncSession,
        asset_id: UUID,
        current_user: User,
    ) -> Asset:
        result = await db.execute(
            select(Asset).join(Project, Asset.project_id == Project.id).where(Asset.id == asset_id)
        )
        asset = result.scalar_one_or_none()

        if not asset:
            raise NotFoundError("Asset not found")

        # Check project ownership
        proj_res = await db.execute(select(Project).where(Project.id == asset.project_id))
        project = proj_res.scalar_one()
        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have access to this asset")

        return asset

    @classmethod
    async def create_asset(
        cls,
        db: AsyncSession,
        project_id: UUID,
        req: AssetCreate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Asset:
        # Verify project exists and belongs to user
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to add assets to this project")

        # Enforce authorization confirmation
        if not req.authorization_confirmed:
            raise ValidationError("You must confirm authorization before registering this asset for security assessment")

        # Validate target format
        cls.validate_asset_target(req.type, req.target)

        asset = Asset(
            project_id=project_id,
            name=req.name,
            type=req.type,
            target=req.target.strip(),
            description=req.description,
            authorization_confirmed=True,
            status=AssetStatus.ACTIVE,
        )
        db.add(asset)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="asset.created",
            user_id=current_user.id,
            resource_type="asset",
            resource_id=str(asset.id),
            metadata={"name": asset.name, "type": asset.type.value, "target": asset.target},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return asset

    @classmethod
    async def update_asset(
        cls,
        db: AsyncSession,
        asset_id: UUID,
        req: AssetUpdate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Asset:
        asset = await cls.get_asset_by_id(db, asset_id, current_user)

        if req.name is not None:
            asset.name = req.name
        if req.target is not None:
            cls.validate_asset_target(asset.type, req.target)
            asset.target = req.target.strip()
        if req.description is not None:
            asset.description = req.description
        if req.status is not None:
            asset.status = req.status

        await db.flush()

        await AuditService.log_event(
            db=db,
            action="asset.updated",
            user_id=current_user.id,
            resource_type="asset",
            resource_id=str(asset.id),
            metadata={"name": asset.name, "status": asset.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return asset

    @classmethod
    async def delete_asset(
        cls,
        db: AsyncSession,
        asset_id: UUID,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        asset = await cls.get_asset_by_id(db, asset_id, current_user)

        await db.delete(asset)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="asset.deleted",
            user_id=current_user.id,
            resource_type="asset",
            resource_id=str(asset_id),
            metadata={"name": asset.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
