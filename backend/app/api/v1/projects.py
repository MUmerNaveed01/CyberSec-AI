from uuid import UUID
from math import ceil
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetListResponse,
)
from app.services.project_service import ProjectService
from app.services.asset_service import AssetService
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

@router.get("", response_model=ProjectListResponse, summary="List security projects")
async def list_projects(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    projects, total = await ProjectService.get_projects(
        db, current_user, offset=pagination.offset, limit=pagination.page_size
    )
    pages = ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": projects,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new security assessment project",
)
async def create_project(
    req: ProjectCreate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    return await ProjectService.create_project(
        db, req, current_user, ip_address=ip, user_agent=ua
    )

@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project details")
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService.get_project_by_id(db, project_id, current_user)

@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: UUID,
    req: ProjectUpdate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    return await ProjectService.update_project(
        db, project_id, req, current_user, ip_address=ip, user_agent=ua
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(
    project_id: UUID,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    await ProjectService.delete_project(
        db, project_id, current_user, ip_address=ip, user_agent=ua
    )
    return None

# Project Asset Endpoints
@router.get("/{project_id}/assets", response_model=AssetListResponse, summary="List project assets")
async def list_project_assets(
    project_id: UUID,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify access to project first
    await ProjectService.get_project_by_id(db, project_id, current_user)
    assets, total = await AssetService.get_assets(
        db, current_user, project_id=project_id, offset=pagination.offset, limit=pagination.page_size
    )
    pages = ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": [AssetResponse.model_validate(a) for a in assets],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.post(
    "/{project_id}/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new authorized asset under project",
)
async def create_project_asset(
    project_id: UUID,
    req: AssetCreate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    asset = await AssetService.create_asset(
        db, project_id, req, current_user, ip_address=ip, user_agent=ua
    )
    return AssetResponse.model_validate(asset)
