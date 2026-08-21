from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.project import Project, ProjectStatus
from app.models.asset import Asset
from app.models.scan import Scan
from app.models.finding import Finding, FindingSeverity, FindingStatus
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStats
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProjectService:
    @staticmethod
    async def get_project_stats(db: AsyncSession, project_id: UUID) -> ProjectStats:
        # Asset count
        asset_count_res = await db.execute(
            select(func.count(Asset.id)).where(Asset.project_id == project_id)
        )
        assets_count = asset_count_res.scalar_one()

        # Scan count
        scan_count_res = await db.execute(
            select(func.count(Scan.id)).where(Scan.project_id == project_id)
        )
        scans_count = scan_count_res.scalar_one()

        # Findings counts by severity for active assets in project
        findings_query = (
            select(Finding.severity, func.count(Finding.id))
            .join(Asset, Finding.asset_id == Asset.id)
            .where(
                Asset.project_id == project_id,
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.IN_PROGRESS]),
            )
            .group_by(Finding.severity)
        )
        findings_res = await db.execute(findings_query)
        severity_counts = {sev: count for sev, count in findings_res.all()}

        critical = severity_counts.get(FindingSeverity.CRITICAL, 0)
        high = severity_counts.get(FindingSeverity.HIGH, 0)
        medium = severity_counts.get(FindingSeverity.MEDIUM, 0)
        low = severity_counts.get(FindingSeverity.LOW, 0)

        # Deterministic security score: Starts at 100, deducted by findings
        penalty = (critical * 25) + (high * 15) + (medium * 5) + (low * 1)
        security_score = max(0, 100 - penalty)

        return ProjectStats(
            security_score=security_score,
            assets_count=assets_count,
            scans_count=scans_count,
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
        )

    @classmethod
    async def get_projects(
        cls,
        db: AsyncSession,
        current_user: User,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query = select(Project)
        count_query = select(func.count(Project.id))

        if current_user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == current_user.id)
            count_query = count_query.where(Project.owner_id == current_user.id)

        query = query.order_by(desc(Project.created_at)).offset(offset).limit(limit)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        projects_res = await db.execute(query)
        projects = projects_res.scalars().all()

        results = []
        for proj in projects:
            stats = await cls.get_project_stats(db, proj.id)
            proj_dict = {
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "owner_id": proj.owner_id,
                "status": proj.status,
                "created_at": proj.created_at,
                "updated_at": proj.updated_at,
                "stats": stats,
            }
            results.append(proj_dict)

        return results, total

    @classmethod
    async def get_project_by_id(
        cls,
        db: AsyncSession,
        project_id: UUID,
        current_user: User,
    ) -> dict:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have access to this project")

        stats = await cls.get_project_stats(db, project.id)
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "stats": stats,
        }

    @classmethod
    async def create_project(
        cls,
        db: AsyncSession,
        req: ProjectCreate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        project = Project(
            name=req.name,
            description=req.description,
            owner_id=current_user.id,
            status=ProjectStatus.ACTIVE,
        )
        db.add(project)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="project.created",
            user_id=current_user.id,
            resource_type="project",
            resource_id=str(project.id),
            metadata={"name": project.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "stats": ProjectStats(),
        }

    @classmethod
    async def update_project(
        cls,
        db: AsyncSession,
        project_id: UUID,
        req: ProjectUpdate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to modify this project")

        if req.name is not None:
            project.name = req.name
        if req.description is not None:
            project.description = req.description
        if req.status is not None:
            project.status = req.status

        await db.flush()

        await AuditService.log_event(
            db=db,
            action="project.updated",
            user_id=current_user.id,
            resource_type="project",
            resource_id=str(project.id),
            metadata={"name": project.name, "status": project.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await cls.get_project_by_id(db, project_id, current_user)

    @classmethod
    async def delete_project(
        cls,
        db: AsyncSession,
        project_id: UUID,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to delete this project")

        await db.delete(project)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="project.deleted",
            user_id=current_user.id,
            resource_type="project",
            resource_id=str(project_id),
            metadata={"name": project.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
