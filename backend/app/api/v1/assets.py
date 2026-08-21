from uuid import UUID
from math import ceil
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.asset import (
    AssetUpdate,
    AssetResponse,
    AssetListResponse,
)
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

@router.get("", response_model=AssetListResponse, summary="List all accessible assets")
async def list_assets(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    assets, total = await AssetService.get_assets(
        db, current_user, offset=pagination.offset, limit=pagination.page_size
    )
    pages = ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": [AssetResponse.model_validate(a) for a in assets],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }

@router.get("/{asset_id}", response_model=AssetResponse, summary="Get asset by ID")
async def get_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await AssetService.get_asset_by_id(db, asset_id, current_user)
    return AssetResponse.model_validate(asset)

@router.patch("/{asset_id}", response_model=AssetResponse, summary="Update asset")
async def update_asset(
    asset_id: UUID,
    req: AssetUpdate,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    asset = await AssetService.update_asset(
        db, asset_id, req, current_user, ip_address=ip, user_agent=ua
    )
    return AssetResponse.model_validate(asset)

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete asset")
async def delete_asset(
    asset_id: UUID,
    request: Request,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    await AssetService.delete_asset(
        db, asset_id, current_user, ip_address=ip, user_agent=ua
    )
    return None
