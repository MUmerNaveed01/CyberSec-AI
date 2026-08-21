from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.api.v1.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

def get_client_info(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    if "x-forwarded-for" in request.headers:
        ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    user_agent = request.headers.get("user-agent")
    return ip, user_agent

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    req: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    user = await AuthService.register_user(db, req, ip_address=ip, user_agent=ua)
    return AuthService.create_tokens_for_user(user)

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    req: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    user = await AuthService.authenticate_user(
        db, req.email, req.password, ip_address=ip, user_agent=ua
    )
    return AuthService.create_tokens_for_user(user)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    req: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    return await AuthService.refresh_tokens(
        db, req.refresh_token, ip_address=ip, user_agent=ua
    )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out user",
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    ip, ua = get_client_info(request)
    await AuditService.log_event(
        db=db,
        action="auth.logout",
        user_id=current_user.id,
        metadata={"email": current_user.email},
        ip_address=ip,
        user_agent=ua,
    )
    return {"message": "Successfully logged out"}

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return UserResponse.model_validate(current_user)
