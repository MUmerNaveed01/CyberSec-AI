"""
Admin API — Audit Logs, User Management, Platform Settings
Only ADMIN role can access these endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.api.v1.deps import require_admin, get_current_active_user
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.pagination import PaginationParams
from app.core.exceptions import NotFoundError, ForbiddenError
from pydantic import BaseModel

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata_: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: AuditLog) -> "AuditLogResponse":
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            action=obj.action,
            resource_type=obj.resource_type,
            resource_id=obj.resource_id,
            metadata_=obj.metadata_,
            ip_address=obj.ip_address,
            user_agent=obj.user_agent,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
        )


class UserAdminResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: User) -> "UserAdminResponse":
        return cls(
            id=obj.id,
            name=obj.name,
            email=obj.email,
            role=obj.role.value,
            is_active=obj.is_active,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
        )


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


# ─── Audit Logs ───────────────────────────────────────────────────────────────

@router.get("/audit-logs", summary="List audit logs (Admin only)")
async def list_audit_logs(
    action: str | None = Query(None, description="Filter by action type"),
    user_id: UUID | None = Query(None, description="Filter by user"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    count_query = select(func.count(AuditLog.id))

    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
        count_query = count_query.where(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query.offset(offset).limit(page_size))
    logs = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": [AuditLogResponse.from_orm_obj(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


# ─── User Management ──────────────────────────────────────────────────────────

@router.get("/users", summary="List all users (Admin only)")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(User).order_by(User.created_at).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": [UserAdminResponse.from_orm_obj(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.patch("/users/{user_id}/role", summary="Update user role (Admin only)")
async def update_user_role(
    user_id: UUID,
    req: UpdateUserRoleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    if user.id == current_user.id:
        raise ForbiddenError("You cannot change your own role")
    user.role = req.role
    await db.flush()
    return UserAdminResponse.from_orm_obj(user)


@router.patch("/users/{user_id}/status", summary="Enable/disable user (Admin only)")
async def update_user_status(
    user_id: UUID,
    req: UpdateUserStatusRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    if user.id == current_user.id:
        raise ForbiddenError("You cannot change your own status")
    user.is_active = req.is_active
    await db.flush()
    return UserAdminResponse.from_orm_obj(user)


# ─── Platform Stats (for settings page) ───────────────────────────────────────

@router.get("/stats", summary="Platform-wide statistics")
async def platform_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.project import Project
    from app.models.asset import Asset
    from app.models.scan import Scan, ScanStatus
    from app.models.finding import Finding

    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    project_count = (await db.execute(select(func.count(Project.id)))).scalar_one()
    asset_count = (await db.execute(select(func.count(Asset.id)))).scalar_one()
    scan_count = (await db.execute(select(func.count(Scan.id)))).scalar_one()
    finding_count = (await db.execute(select(func.count(Finding.id)))).scalar_one()
    audit_count = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()

    return {
        "users": user_count,
        "projects": project_count,
        "assets": asset_count,
        "scans": scan_count,
        "findings": finding_count,
        "audit_logs": audit_count,
        "version": "0.1.0",
        "app_name": "AI Cybersecurity Assessment Platform",
    }
