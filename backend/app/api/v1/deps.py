from typing import Annotated, Sequence
from uuid import UUID
from fastapi import Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import decode_token
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.schemas.pagination import PaginationParams

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    token_auth: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None
    if token_auth:
        token = token_auth.credentials
    elif "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise UnauthorizedError("Missing authentication credentials")

    payload = decode_token(token, settings.JWT_SECRET_KEY)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Invalid or expired authentication token")

    user_id_str = payload.get("sub")
    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid token subject")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User does not exist")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise UnauthorizedError("Inactive user")
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: Sequence[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise ForbiddenError("You do not have sufficient permissions to access this resource")
        return user

# RBAC Dependencies
require_admin = RoleChecker([UserRole.ADMIN])
require_analyst = RoleChecker([UserRole.ADMIN, UserRole.ANALYST])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])

# Common parameter dependencies

