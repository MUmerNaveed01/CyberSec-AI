import os
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.models.finding import Finding
from app.models.ai_analysis import AIAnalysis
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

class AIService:
    @staticmethod
    def _generate_rule_based_analysis(finding: Finding) -> dict:
        """Deterministic, reliable cybersecurity analyst analysis without hallucination"""
        category_impacts = {
            "CRYPTOGRAPHY": "Insecure cryptographic channels enable interception, tampering, and credential theft by network adversaries.",
            "CONFIGURATION": "Improper server configuration exposes attack surfaces and decreases defensive resilience against automated scanners.",
            "SECRETS": "Exposed keys allow unauthorized access to infrastructure, data exfiltration, and potential lateral movement.",
            "DEPENDENCY": "Known public CVE vulnerabilities can be easily exploited using pre-existing exploit scripts and automated tools.",
            "AUTHENTICATION": "Weaknesses in authentication or cookie flags allow session hijacking and impersonation of authorized personnel.",
        }

        impact = category_impacts.get(
            finding.category.value,
            "May permit unauthorized access or security policy circumvention depending on environmental factors."
        )

        priority_map = {
            "CRITICAL": "P0 - Immediate Hotfix Required",
            "HIGH": "P1 - Remediate within 24-48 Hours",
            "MEDIUM": "P2 - Remediate in Current Sprint",
            "LOW": "P3 - Remediate in Next Maintenance Window",
            "INFO": "P4 - Informational / Best Practice",
        }

        priority = priority_map.get(finding.severity.value, "P2 - Standard Priority")

        tech_expl = (
            f"The scanner identified '{finding.title}' with confidence {finding.confidence*100:.0f}%. "
            f"Evidence: {finding.evidence}. "
            f"Under {finding.cwe or 'standard security benchmarks'}, this violates defensive baselines."
        )

        return {
            "summary": f"Security Assessment: {finding.title} detected on target asset with risk score {finding.risk_score}/10.",
            "technical_explanation": tech_expl,
            "business_impact": impact,
            "remediation": finding.remediation,
            "priority": priority,
            "model": "CyberSec-Rule-Analyst-v1",
        }

    @classmethod
    async def analyze_finding(cls, db: AsyncSession, finding_id: UUID) -> AIAnalysis:
        result = await db.execute(select(Finding).where(Finding.id == finding_id))
        finding = result.scalar_one_or_none()
        if not finding:
            raise NotFoundError("Finding not found")

        # Check if already analyzed
        existing_res = await db.execute(select(AIAnalysis).where(AIAnalysis.finding_id == finding_id))
        existing = existing_res.scalar_one_or_none()
        if existing:
            return existing

        # If external AI key is available, we could invoke LLM API; otherwise fallback to the deterministic analysis
        analysis_data = cls._generate_rule_based_analysis(finding)

        analysis = AIAnalysis(
            finding_id=finding.id,
            summary=analysis_data["summary"],
            technical_explanation=analysis_data["technical_explanation"],
            business_impact=analysis_data["business_impact"],
            remediation=analysis_data["remediation"],
            priority=analysis_data["priority"],
            model=analysis_data["model"],
            created_at=datetime.now(timezone.utc),
        )
        db.add(analysis)
        await db.flush()

        return analysis
