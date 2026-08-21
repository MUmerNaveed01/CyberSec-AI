import re
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.asset import AssetType, AssetStatus

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: AssetType
    target: str = Field(..., min_length=1, max_length=1000)
    description: str | None = Field(None, max_length=500)
    authorization_confirmed: bool = Field(
        ...,
        description="Explicit user confirmation that they own or are authorized to test this target",
    )

    @field_validator("authorization_confirmed")
    @classmethod
    def validate_authorization(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "You must explicitly confirm that you own or have authorization to test this target."
            )
        return v

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        target = v.strip()
        if not target:
            raise ValueError("Target cannot be empty")
        return target

class AssetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    target: str | None = Field(None, min_length=1, max_length=1000)
    description: str | None = Field(None, max_length=500)
    status: AssetStatus | None = None

class AssetResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    type: AssetType
    target: str
    description: str | None = None
    authorization_confirmed: bool
    status: AssetStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    pages: int
