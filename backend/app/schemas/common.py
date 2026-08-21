from pydantic import BaseModel
from typing import Any

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

class HealthStatus(BaseModel):
    status: str
    version: str
    services: dict[str, str]
    timestamp: str

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
