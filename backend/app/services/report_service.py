import os
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.models.report import Report, ReportType
from app.models.project import Project
from app.models.finding import Finding
from app.models.asset import Asset
from app.models.user import User, UserRole
from app.schemas.report import ReportCreate
from app.services.project_service import ProjectService
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class ReportService:
    @staticmethod
    async def generate_markdown_report(
        db: AsyncSession,
        project: Project,
        report_type: ReportType,
        findings: list[Finding],
    ) -> str:
        stats = await ProjectService.get_project_stats(db, project.id)

        md = []
        md.append(f"# Cybersecurity Assessment Report — {project.name}")
        md.append(f"**Report Type**: {report_type.value} | **Assessment Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**Overall Security Score**: {stats.security_score}/100\n")
        md.append("---")
        md.append("## Executive Summary")
        md.append(f"An automated defensive security assessment was conducted against assets in project **{project.name}**.")
        md.append(f"- **Total Assets Tested**: {stats.assets_count}")
        md.append(f"- **Critical Vulnerabilities**: {stats.critical_findings}")
        md.append(f"- **High Vulnerabilities**: {stats.high_findings}")
        md.append(f"- **Medium Vulnerabilities**: {stats.medium_findings}")
        md.append(f"- **Low Vulnerabilities**: {stats.low_findings}\n")

        if report_type in [ReportType.TECHNICAL, ReportType.FULL]:
            md.append("---")
            md.append("## Detailed Vulnerability Findings")
            if not findings:
                md.append("No active vulnerabilities identified in the tested scope.")
            else:
                for idx, f in enumerate(findings, 1):
                    md.append(f"### {idx}. [{f.severity.value}] {f.title}")
                    md.append(f"- **Risk Score**: {f.risk_score} / 10.0")
                    md.append(f"- **Category**: {f.category.value} | **Status**: {f.status.value}")
                    if f.cwe:
                        md.append(f"- **CWE**: {f.cwe}")
                    if f.cve:
                        md.append(f"- **CVE**: {f.cve}")
                    md.append(f"\n**Description**:\n{f.description}\n")
                    md.append(f"**Remediation Recommendation**:\n{f.remediation}\n")

        return "\n".join(md)

    @classmethod
    async def create_report(
        cls,
        db: AsyncSession,
        req: ReportCreate,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Report:
        proj_res = await db.execute(select(Project).where(Project.id == req.project_id))
        project = proj_res.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project not found")

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("Access denied")

        # Fetch findings
        findings_query = (
            select(Finding)
            .join(Asset, Finding.asset_id == Asset.id)
            .where(Asset.project_id == project.id)
            .order_by(desc(Finding.risk_score))
        )
        findings_res = await db.execute(findings_query)
        findings = list(findings_res.scalars().all())

        report_content = await cls.generate_markdown_report(db, project, req.report_type, findings)

        report = Report(
            project_id=project.id,
            scan_id=req.scan_id,
            report_type=req.report_type,
            file_path=None,
            generated_by=current_user.id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)
        await db.flush()

        await AuditService.log_event(
            db=db,
            action="report.generated",
            user_id=current_user.id,
            resource_type="report",
            resource_id=str(report.id),
            metadata={"project_id": str(project.id), "report_type": report.report_type.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return report

    @classmethod
    async def get_reports(
        cls,
        db: AsyncSession,
        current_user: User,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        query = select(Report).join(Project, Report.project_id == Project.id)
        count_query = select(func.count(Report.id)).join(Project, Report.project_id == Project.id)

        if project_id:
            query = query.where(Report.project_id == project_id)
            count_query = count_query.where(Report.project_id == project_id)

        if current_user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == current_user.id)
            count_query = count_query.where(Project.owner_id == current_user.id)

        query = query.order_by(desc(Report.created_at)).offset(offset).limit(limit)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        reports_res = await db.execute(query)
        reports = reports_res.scalars().all()

        return list(reports), total

    @classmethod
    async def get_report_by_id(
        cls,
        db: AsyncSession,
        report_id: UUID,
        current_user: User,
    ) -> dict:
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            raise NotFoundError("Report not found")

        proj_res = await db.execute(select(Project).where(Project.id == report.project_id))
        project = proj_res.scalar_one()

        if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("Access denied")

        # Generate content for view/download
        findings_query = (
            select(Finding)
            .join(Asset, Finding.asset_id == Asset.id)
            .where(Asset.project_id == project.id)
            .order_by(desc(Finding.risk_score))
        )
        findings_res = await db.execute(findings_query)
        findings = list(findings_res.scalars().all())

        content = await cls.generate_markdown_report(db, project, report.report_type, findings)

        return {
            "id": report.id,
            "project_id": report.project_id,
            "scan_id": report.scan_id,
            "report_type": report.report_type,
            "file_path": report.file_path,
            "generated_by": report.generated_by,
            "created_at": report.created_at,
            "content": content,
        }
