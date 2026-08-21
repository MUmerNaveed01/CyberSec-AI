import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, Request, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanListResponse,
)
from app.services.scan_service import ScanService
from app.workers.scan_tasks import run_scan_async
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

@router.get("", response_model=ScanListResponse, summary="List scans")
async def list_scans(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    scans, total = await ScanService.get_scans(
        db, current_user, offset=pagination.offset, limit=pagination.page_size
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    return {
        "items": [ScanResponse.model_validate(s) for s in scans],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch a security assessment scan",
)
async def launch_scan(
    req: ScanCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    scan = await ScanService.create_scan(
        db, req, current_user, ip_address=ip, user_agent=ua
    )

    # Execute scan synchronously using the current request DB session
    await run_scan_async(scan.id, db_session=db)

    # Refresh scan status after execution
    refreshed_scan = await ScanService.get_scan_by_id(db, scan.id, current_user)
    return ScanResponse.model_validate(refreshed_scan)

@router.get("/{scan_id}", response_model=ScanResponse, summary="Get scan status and details")
async def get_scan(
    scan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    scan = await ScanService.get_scan_by_id(db, scan_id, current_user)
    return ScanResponse.model_validate(scan)

@router.post("/{scan_id}/cancel", response_model=ScanResponse, summary="Cancel an in-progress scan")
async def cancel_scan(
    scan_id: UUID,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    scan = await ScanService.cancel_scan(
        db, scan_id, current_user, ip_address=ip, user_agent=ua
    )
    return ScanResponse.model_validate(scan)
