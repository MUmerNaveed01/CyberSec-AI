from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.asset import Asset
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.scan import ScanCreate
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class ScanService:
    @classmethod
    async def create_scan(
        cls,
        db: AsyncSession,
        req: ScanCreate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Scan:
        # Validate Project
        proj_res = await db.execute(select(Project).where(Project.id == req.project_id))
        project = proj_res.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to run scans on this project")

        # Validate Asset
        asset_res = await db.execute(select(Asset).where(Asset.id == req.asset_id))
        asset = asset_res.scalar_one_or_none()
        if not asset or asset.project_id != req.project_id:
            raise NotFoundError("Asset not found in this project")

        if not asset.authorization_confirmed:
            raise ValidationError("Cannot scan an asset without confirmed authorization")

        # Compatibility check between scan_type and asset_type
        if req.scan_type == ScanType.WEBSITE and asset.type.value != "WEBSITE":
            raise ValidationError("Website scan requires an asset of type WEBSITE")
        if req.scan_type == ScanType.SECRETS and asset.type.value not in ["SOURCE_CODE", "DEPENDENCY_MANIFEST"]:
            raise ValidationError("Secrets scan requires SOURCE_CODE or DEPENDENCY_MANIFEST asset")
        if req.scan_type == ScanType.DEPENDENCIES and asset.type.value not in ["DEPENDENCY_MANIFEST", "SOURCE_CODE"]:
            raise ValidationError("Dependency scan requires a DEPENDENCY_MANIFEST or SOURCE_CODE asset")

        scan = Scan(
            project_id=req.project_id,
            asset_id=req.asset_id,
            scan_type=req.scan_type,
            status=ScanStatus.QUEUED,
            progress=0,
            created_by=current_user.id,
        )
        db.add(scan)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="scan.queued",
            user_id=current_user.id,
            resource_type="scan",
            resource_id=str(scan.id),
            metadata={"scan_type": scan.scan_type.value, "asset_id": str(asset.id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return scan

    @classmethod
    async def get_scans(
        cls,
        db: AsyncSession,
        current_user: User,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Scan], int]:
        query = select(Scan).join(Project, Scan.project_id == Project.id)
        count_query = select(func.count(Scan.id)).join(Project, Scan.project_id == Project.id)

        if project_id:
            query = query.where(Scan.project_id == project_id)
            count_query = count_query.where(Scan.project_id == project_id)

        if current_user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == current_user.id)
            count_query = count_query.where(Project.owner_id == current_user.id)

        query = query.order_by(desc(Scan.created_at)).offset(offset).limit(limit)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        scans_res = await db.execute(query)
        scans = scans_res.scalars().all()

        return list(scans), total

    @classmethod
    async def get_scan_by_id(
        cls,
        db: AsyncSession,
        scan_id: UUID,
        current_user: User,
    ) -> Scan:
        query = select(Scan).join(Project, Scan.project_id == Project.id).where(Scan.id == scan_id)
        result = await db.execute(query)
        scan = result.scalar_one_or_none()

        if not scan:
            raise NotFoundError("Scan not found")

        # Verify access
        proj_res = await db.execute(select(Project).where(Project.id == scan.project_id))
        project = proj_res.scalar_one()
        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have access to this scan")

        return scan

    @classmethod
    async def cancel_scan(
        cls,
        db: AsyncSession,
        scan_id: UUID,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Scan:
        scan = await cls.get_scan_by_id(db, scan_id, current_user)

        if scan.status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
            raise ValidationError(f"Cannot cancel scan that is already {scan.status.value}")

        scan.status = ScanStatus.CANCELLED
        scan.completed_at = datetime.now(timezone.utc)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="scan.cancelled",
            user_id=current_user.id,
            resource_type="scan",
            resource_id=str(scan.id),
            metadata={"scan_id": str(scan.id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return scan
