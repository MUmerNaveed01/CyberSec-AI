from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 500):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(self.message)

class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, http_status=404)

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(code="UNAUTHORIZED", message=message, http_status=401)

class ForbiddenError(AppError):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(code="FORBIDDEN", message=message, http_status=403)

class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(code="VALIDATION_ERROR", message=message, http_status=422)

class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(code="CONFLICT", message=message, http_status=409)

async def exception_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
