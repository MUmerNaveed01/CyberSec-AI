from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from app.models.asset import AssetType, Asset
from app.models.finding import FindingSeverity, FindingCategory

class RawFinding(BaseModel):
    title: str
    description: str
    category: FindingCategory
    severity: FindingSeverity
    confidence: float
    evidence: dict[str, Any]
    remediation: str
    cwe: str | None = None
    cve: str | None = None

class ScannerResult(BaseModel):
    scanner_name: str
    scanner_version: str
    target: str
    success: bool
    findings: list[RawFinding]
    metadata: dict[str, Any] = {}
    error_message: str | None = None

class BaseScanner(ABC):
    @property
    @abstractmethod
    def scanner_name(self) -> str:
        """Name of the security scanner"""
        pass

    @property
    @abstractmethod
    def scanner_version(self) -> str:
        """Version of the security scanner"""
        pass

    @property
    @abstractmethod
    def supported_asset_types(self) -> list[AssetType]:
        """List of asset types this scanner can inspect"""
        pass

    @abstractmethod
    async def execute(self, asset: Asset) -> ScannerResult:
        """Execute the security assessment against the target asset"""
        pass
