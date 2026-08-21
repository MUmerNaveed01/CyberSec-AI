from uuid import UUID
from datetime import datetime, timezone
from app.models.finding import Finding, FindingSeverity, FindingStatus, FindingCategory
from app.scanners.base import RawFinding

class RiskEngine:
    @staticmethod
    def calculate_risk_score(
        severity: FindingSeverity,
        confidence: float,
        category: FindingCategory,
    ) -> float:
        # Base score from severity
        severity_bases = {
            FindingSeverity.CRITICAL: 9.5,
            FindingSeverity.HIGH: 8.0,
            FindingSeverity.MEDIUM: 5.5,
            FindingSeverity.LOW: 2.5,
            FindingSeverity.INFO: 0.5,
        }
        base = severity_bases.get(severity, 1.0)

        # Weight by confidence (0.5 to 1.0)
        confidence_factor = max(0.5, min(confidence, 1.0))
        calculated = base * confidence_factor
        return round(min(10.0, max(0.1, calculated)), 1)

class FindingNormalizer:
    @staticmethod
    def normalize_raw_finding(
        raw: RawFinding,
        scan_id: UUID,
        asset_id: UUID,
    ) -> Finding:
        risk_score = RiskEngine.calculate_risk_score(
            severity=raw.severity,
            confidence=raw.confidence,
            category=raw.category,
        )

        now = datetime.now(timezone.utc)
        return Finding(
            scan_id=scan_id,
            asset_id=asset_id,
            title=raw.title,
            description=raw.description,
            category=raw.category,
            severity=raw.severity,
            confidence=raw.confidence,
            evidence=raw.evidence,
            remediation=raw.remediation,
            cwe=raw.cwe,
            cve=raw.cve,
            status=FindingStatus.OPEN,
            risk_score=risk_score,
            first_seen_at=now,
            last_seen_at=now,
        )
