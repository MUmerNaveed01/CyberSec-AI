import ssl
import socket
import httpx
from datetime import datetime, timezone
from app.models.asset import Asset, AssetType
from app.models.finding import FindingSeverity, FindingCategory
from app.scanners.base import BaseScanner, ScannerResult, RawFinding
from app.core.ssrf import SSRFProtection
from app.core.logging import get_logger

logger = get_logger(__name__)

class WebsiteScanner(BaseScanner):
    @property
    def scanner_name(self) -> str:
        return "Website Security Configuration Scanner"

    @property
    def scanner_version(self) -> str:
        return "1.0.0"

    @property
    def supported_asset_types(self) -> list[AssetType]:
        return [AssetType.WEBSITE]

    async def execute(self, asset: Asset) -> ScannerResult:
        target_url = asset.target.strip()
        findings: list[RawFinding] = []

        try:
            # Enforce SSRF check prior to connection
            SSRFProtection.validate_url(target_url)
        except Exception as e:
            return ScannerResult(
                scanner_name=self.scanner_name,
                scanner_version=self.scanner_version,
                target=target_url,
                success=False,
                findings=[],
                error_message=f"SSRF validation blocked target: {str(e)}",
            )

        # 1. Check HTTPS Enforcement & TLS
        if target_url.startswith("http://"):
            findings.append(
                RawFinding(
                    title="Insecure HTTP Protocol Configured",
                    description="The target website URL is configured with plaintext HTTP instead of secure HTTPS.",
                    category=FindingCategory.CRYPTOGRAPHY,
                    severity=FindingSeverity.HIGH,
                    confidence=1.0,
                    evidence={"configured_url": target_url, "protocol": "http"},
                    remediation="Migrate all traffic to HTTPS and configure 301 redirects from HTTP to HTTPS.",
                    cwe="CWE-319",
                )
            )

        # 2. Inspect HTTP Security Headers and Cookie configurations
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                max_redirects=5,
                verify=True,
            ) as client:
                response = await client.get(target_url)
                headers = {k.lower(): v for k, v in response.headers.items()}

                # Check Strict-Transport-Security (HSTS)
                if "strict-transport-security" not in headers:
                    findings.append(
                        RawFinding(
                            title="Missing HTTP Strict Transport Security (HSTS)",
                            description="The server does not send the Strict-Transport-Security header, leaving users vulnerable to SSL stripping attacks.",
                            category=FindingCategory.CONFIGURATION,
                            severity=FindingSeverity.MEDIUM,
                            confidence=1.0,
                            evidence={"headers_received": list(headers.keys())},
                            remediation="Add the header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
                            cwe="CWE-523",
                        )
                    )

                # Check Content-Security-Policy (CSP)
                if "content-security-policy" not in headers:
                    findings.append(
                        RawFinding(
                            title="Missing Content Security Policy (CSP)",
                            description="No Content-Security-Policy header detected. CSP mitigates Cross-Site Scripting (XSS) and data injection attacks.",
                            category=FindingCategory.CONFIGURATION,
                            severity=FindingSeverity.MEDIUM,
                            confidence=1.0,
                            evidence={"headers_received": list(headers.keys())},
                            remediation="Define and configure a strict Content-Security-Policy header restricting script and resource sources.",
                            cwe="CWE-1021",
                        )
                    )

                # Check X-Content-Type-Options
                if headers.get("x-content-type-options", "").lower() != "nosniff":
                    findings.append(
                        RawFinding(
                            title="Missing X-Content-Type-Options Header",
                            description="The X-Content-Type-Options header is not set to 'nosniff'. Browsers may perform MIME-type sniffing and execute untrusted files.",
                            category=FindingCategory.CONFIGURATION,
                            severity=FindingSeverity.LOW,
                            confidence=1.0,
                            evidence={"current_value": headers.get("x-content-type-options", "None")},
                            remediation="Configure header: X-Content-Type-Options: nosniff",
                            cwe="CWE-79",
                        )
                    )

                # Check X-Frame-Options / Frame Ancestors
                if "x-frame-options" not in headers and "frame-ancestors" not in headers.get("content-security-policy", ""):
                    findings.append(
                        RawFinding(
                            title="Missing Clickjacking Defense (X-Frame-Options)",
                            description="The application does not specify X-Frame-Options or CSP frame-ancestors, permitting framing inside third-party iframes.",
                            category=FindingCategory.CONFIGURATION,
                            severity=FindingSeverity.MEDIUM,
                            confidence=1.0,
                            evidence={"headers_received": list(headers.keys())},
                            remediation="Set X-Frame-Options: DENY or SAMEORIGIN.",
                            cwe="CWE-1021",
                        )
                    )

                # Check Server / Technology Information Disclosure
                server_hdr = headers.get("server")
                x_powered_by = headers.get("x-powered-by")
                if server_hdr or x_powered_by:
                    findings.append(
                        RawFinding(
                            title="Server Banner & Technology Information Disclosure",
                            description="The web server exposes software version headers (Server or X-Powered-By), aiding attackers in fingerprinting.",
                            category=FindingCategory.SENSITIVE_DATA,
                            severity=FindingSeverity.INFO,
                            confidence=0.9,
                            evidence={
                                "server": server_hdr,
                                "x_powered_by": x_powered_by,
                            },
                            remediation="Disable server signature banners and remove X-Powered-By headers in web server configuration.",
                            cwe="CWE-200",
                        )
                    )

                # Check Cookie Security Flags
                for cookie_name, cookie_val in response.cookies.items():
                    raw_cookie_header = response.headers.get("set-cookie", "")
                    if "secure" not in raw_cookie_header.lower():
                        findings.append(
                            RawFinding(
                                title=f"Insecure Cookie Missing 'Secure' Flag ({cookie_name})",
                                description=f"Cookie '{cookie_name}' was transmitted without the 'Secure' attribute, risking interception over plaintext channels.",
                                category=FindingCategory.AUTHENTICATION,
                                severity=FindingSeverity.LOW,
                                confidence=0.9,
                                evidence={"cookie_name": cookie_name},
                                remediation="Add the 'Secure' flag to all session and sensitive cookies.",
                                cwe="CWE-614",
                            )
                        )

            return ScannerResult(
                scanner_name=self.scanner_name,
                scanner_version=self.scanner_version,
                target=target_url,
                success=True,
                findings=findings,
                metadata={
                    "status_code": response.status_code,
                    "scanned_at": datetime.now(timezone.utc).isoformat(),
                    "findings_count": len(findings),
                },
            )

        except Exception as e:
            logger.error("Website scan failed", error=str(e), target=target_url)
            return ScannerResult(
                scanner_name=self.scanner_name,
                scanner_version=self.scanner_version,
                target=target_url,
                success=False,
                findings=findings,
                error_message=f"HTTP connection failed: {str(e)}",
            )
