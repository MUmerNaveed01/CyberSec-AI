from uuid import UUID
from math import ceil
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.models.user import User
from app.models.finding import Finding, FindingSeverity, FindingStatus, FindingCategory
from app.models.asset import Asset
from app.models.project import Project
from app.schemas.finding import (
    FindingUpdate,
    FindingResponse,
    FindingListResponse,
)
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.audit_service import AuditService
from app.api.v1.deps import (
    get_current_active_user,
    require_analyst,
    PaginationParams,
)

router = APIRouter()

def get_client_info(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    if "x-forwarded-for" in request.headers:
        ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    user_agent = request.headers.get("user-agent")
    return ip, user_agent

@router.get("", response_model=FindingListResponse, summary="List findings across assets")
async def list_findings(
    project_id: UUID | None = None,
    asset_id: UUID | None = None,
    severity: FindingSeverity | None = None,
    finding_status: FindingStatus | None = Query(None, alias="status"),
    category: FindingCategory | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).join(Asset, Finding.asset_id == Asset.id).join(Project, Asset.project_id == Project.id)
    count_query = select(func.count(Finding.id)).join(Asset, Finding.asset_id == Asset.id).join(Project, Asset.project_id == Project.id)

    if project_id:
        query = query.where(Project.id == project_id)
        count_query = count_query.where(Project.id == project_id)
    if asset_id:
        query = query.where(Finding.asset_id == asset_id)
        count_query = count_query.where(Finding.asset_id == asset_id)
    if severity:
        query = query.where(Finding.severity == severity)
        count_query = count_query.where(Finding.severity == severity)
    if finding_status:
        query = query.where(Finding.status == finding_status)
        count_query = count_query.where(Finding.status == finding_status)
    if category:
        query = query.where(Finding.category == category)
        count_query = count_query.where(Finding.category == category)

    if current_user.role.value != "ADMIN":
        query = query.where(Project.owner_id == current_user.id)
        count_query = count_query.where(Project.owner_id == current_user.id)

    query = query.order_by(desc(Finding.risk_score), desc(Finding.created_at)).offset(pagination.offset).limit(pagination.page_size)

    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    findings_res = await db.execute(query)
    findings = findings_res.scalars().all()

    pages = ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": [FindingResponse.model_validate(f) for f in findings],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.get("/{finding_id}", response_model=FindingResponse, summary="Get finding by ID")
async def get_finding(
    finding_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).join(Asset, Finding.asset_id == Asset.id).join(Project, Asset.project_id == Project.id).where(Finding.id == finding_id)
    result = await db.execute(query)
    finding = result.scalar_one_or_none()

    if not finding:
        raise NotFoundError("Finding not found")

    return FindingResponse.model_validate(finding)

@router.patch("/{finding_id}", response_model=FindingResponse, summary="Update finding status")
async def update_finding_status(
    finding_id: UUID,
    req: FindingUpdate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).join(Asset, Finding.asset_id == Asset.id).join(Project, Asset.project_id == Project.id).where(Finding.id == finding_id)
    result = await db.execute(query)
    finding = result.scalar_one_or_none()

    if not finding:
        raise NotFoundError("Finding not found")

    old_status = finding.status.value
    if req.status is not None:
        finding.status = req.status

    await db.flush()

    ip, ua = get_client_info(request)
    await AuditService.log_event(
        db=db,
        action="finding.status_updated",
        user_id=current_user.id,
        resource_type="finding",
        resource_id=str(finding.id),
        metadata={"old_status": old_status, "new_status": req.status.value if req.status else None},
        ip_address=ip,
        user_agent=ua,
    )

    return FindingResponse.model_validate(finding)
