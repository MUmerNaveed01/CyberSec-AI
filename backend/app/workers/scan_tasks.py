import asyncio
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.engine import AsyncSessionLocal
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.asset import Asset
from app.scanners.website import WebsiteScanner
from app.scanners.code_and_dependencies import CodeAndDependencyScanner
from app.risk.engine import FindingNormalizer
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def run_scan_async(scan_id: UUID, db_session: AsyncSession | None = None) -> None:
    """Asynchronous scan execution pipeline"""
    if db_session:
        await _execute_scan_with_session(db_session, scan_id)
    else:
        async with AsyncSessionLocal() as db:
            await _execute_scan_with_session(db, scan_id)

async def _execute_scan_with_session(db: AsyncSession, scan_id: UUID) -> None:
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        logger.error("Scan job aborted: Scan record not found", scan_id=str(scan_id))
        return
    asset_res = await db.execute(select(Asset).where(Asset.id == scan.asset_id))
    asset = asset_res.scalar_one_or_none()
    if not asset:
        scan.status = ScanStatus.FAILED
        scan.error_message = "Asset no longer exists"
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()
        return

    try:
        # Mark scan as RUNNING
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        scan.progress = 10
        await db.commit()

        # Execute appropriate scanner
        if scan.scan_type == ScanType.WEBSITE:
            scanner = WebsiteScanner()
        else:
            scanner = CodeAndDependencyScanner()

        scan.progress = 40
        await db.commit()

        scan_result = await scanner.execute(asset)

        scan.progress = 75
        await db.commit()

        if not scan_result.success:
            scan.status = ScanStatus.FAILED
            scan.error_message = scan_result.error_message or "Scan execution failed"
            scan.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        # Normalize and persist findings
        for raw_finding in scan_result.findings:
            finding = FindingNormalizer.normalize_raw_finding(
                raw=raw_finding,
                scan_id=scan.id,
                asset_id=asset.id,
            )
            db.add(finding)

        scan.status = ScanStatus.COMPLETED
        scan.progress = 100
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            "Scan completed successfully",
            scan_id=str(scan.id),
            findings_count=len(scan_result.findings),
        )

    except Exception as e:
        logger.error("Unexpected error during scan execution", error=str(e), scan_id=str(scan_id))
        # Avoid accessing ORM attributes that may trigger lazy loads here
        scan.status = ScanStatus.FAILED
        scan.error_message = str(e)
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()
