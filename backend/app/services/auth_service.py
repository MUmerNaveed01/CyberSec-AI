from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, UserRole
from app.schemas.auth import UserRegisterRequest, TokenResponse, UserResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuthService:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        req: UserRegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == req.email.lower()))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ConflictError("An account with this email already exists")

        # Determine role: make first user ADMIN, subsequent users ANALYST by default
        count_result = await db.execute(select(func.count(User.id)))
        user_count = count_result.scalar_one()
        role = UserRole.ADMIN if user_count == 0 else UserRole.ANALYST

        # Create user
        user = User(
            name=req.name,
            email=req.email.lower(),
            password_hash=hash_password(req.password),
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="auth.register",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"email": user.email, "role": role.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            await AuditService.log_event(
                db=db,
                action="auth.login.failed",
                user_id=user.id if user else None,
                metadata={"email": email},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            await AuditService.log_event(
                db=db,
                action="auth.login.disabled_account",
                user_id=user.id,
                metadata={"email": email},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise UnauthorizedError("Account is inactive. Please contact your administrator.")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="auth.login.success",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"email": user.email},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user

    @classmethod
    def create_tokens_for_user(cls, user: User) -> TokenResponse:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        )

    @classmethod
    async def refresh_tokens(
        cls,
        db: AsyncSession,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
        if not payload or "sub" not in payload:
            raise UnauthorizedError("Invalid or expired refresh token")

        try:
            user_id = UUID(payload["sub"])
        except (ValueError, TypeError):
            raise UnauthorizedError("Invalid token subject")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        await AuditService.log_event(
            db=db,
            action="auth.refresh.success",
            user_id=user.id,
            metadata={"email": user.email},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return cls.create_tokens_for_user(user)
