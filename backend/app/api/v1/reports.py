from uuid import UUID
from math import ceil
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
)
from app.services.report_service import ReportService
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

@router.get("", response_model=ReportListResponse, summary="List security reports")
async def list_reports(
    project_id: UUID | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    reports, total = await ReportService.get_reports(
        db, current_user, project_id=project_id, offset=pagination.offset, limit=pagination.page_size
    )
    pages = ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Generate security report")
async def create_report(
    req: ReportCreate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    report = await ReportService.create_report(
        db, req, current_user, ip_address=ip, user_agent=ua
    )
    return ReportResponse.model_validate(report)

@router.get("/{report_id}", response_model=ReportResponse, summary="Get report details and content")
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    report_dict = await ReportService.get_report_by_id(db, report_id, current_user)
    return ReportResponse(**report_dict)
