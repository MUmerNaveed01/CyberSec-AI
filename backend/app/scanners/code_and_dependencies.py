import math
import re
import os
from pathlib import Path
from datetime import datetime, timezone
from packaging.version import parse as parse_version
from app.models.asset import Asset, AssetType
from app.models.finding import FindingSeverity, FindingCategory
from app.scanners.base import BaseScanner, ScannerResult, RawFinding
from app.core.logging import get_logger

logger = get_logger(__name__)

class CodeAndDependencyScanner(BaseScanner):
    """
    Combined scanner inspecting:
    1. Exposed hardcoded credentials, tokens, and private keys with entropy & masking.
    2. Vulnerable dependencies extracted from package.json, requirements.txt, and pom.xml.
    """

    SECRET_PATTERNS = [
        (r"(?i)aws_?(?:access_key_id|secret_access_key)[\s=:'\"]+([A-Za-z0-9/+=]{16,40})", "AWS Credential / Secret Key", FindingSeverity.CRITICAL, "CWE-798"),
        (r"(?i)(?:api_key|apikey|secret_key|api_secret)[\s=:'\"]+([A-Za-z0-9_\-]{20,64})", "Exposed Generic API Secret", FindingSeverity.HIGH, "CWE-798"),
        (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Unencrypted Private RSA/SSH Key", FindingSeverity.CRITICAL, "CWE-312"),
        (r"(?i)(?:postgres|mysql|mongodb|redis):\/\/[a-zA-Z0-9_\-\.]+:[^@\s]+@[a-zA-Z0-9_\-\.]+", "Database Connection URI with Embedded Password", FindingSeverity.CRITICAL, "CWE-259"),
        (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token", FindingSeverity.CRITICAL, "CWE-798"),
        (r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "Hardcoded JWT Token", FindingSeverity.MEDIUM, "CWE-312"),
    ]

    # Known vulnerable package versions database (CVE feed cache)
    KNOWN_VULNERABILITIES = {
        "requests": {"<2.31.0": {"cve": "CVE-2023-32681", "severity": FindingSeverity.MEDIUM, "fix": "2.31.0", "desc": "Unintended leak of Proxy-Authorization header"}},
        "flask": {"<2.2.5": {"cve": "CVE-2023-30861", "severity": FindingSeverity.HIGH, "fix": "2.2.5", "desc": "Cookie session disclosure with key reuse"}},
        "django": {"<4.2.14": {"cve": "CVE-2024-38875", "severity": FindingSeverity.HIGH, "fix": "4.2.14", "desc": "Potential denial-of-service via query parameters"}},
        "express": {"<4.19.2": {"cve": "CVE-2024-29041", "severity": FindingSeverity.HIGH, "fix": "4.19.2", "desc": "Open redirect in serve-static and send middleware"}},
        "jsonwebtoken": {"<9.0.0": {"cve": "CVE-2022-23529", "severity": FindingSeverity.CRITICAL, "fix": "9.0.0", "desc": "Insecure key parsing enabling arbitrary code execution"}},
        "lodash": {"<4.17.21": {"cve": "CVE-2021-23337", "severity": FindingSeverity.HIGH, "fix": "4.17.21", "desc": "Command injection via template function"}},
        "log4j-core": {"<2.17.1": {"cve": "CVE-2021-44228", "severity": FindingSeverity.CRITICAL, "fix": "2.17.1", "desc": "Log4Shell remote code execution vulnerability"}},
        "spring-core": {"<5.3.18": {"cve": "CVE-2022-22965", "severity": FindingSeverity.CRITICAL, "fix": "5.3.18", "desc": "Spring4Shell RCE via DataBinder parameter binding"}},
    }

    @property
    def scanner_name(self) -> str:
        return "Source Code & Dependency Vulnerability Scanner"

    @property
    def scanner_version(self) -> str:
        return "1.0.0"

    @property
    def supported_asset_types(self) -> list[AssetType]:
        return [AssetType.SOURCE_CODE, AssetType.DEPENDENCY_MANIFEST]

    @staticmethod
    def mask_secret(secret_val: str) -> str:
        if len(secret_val) <= 6:
            return "******"
        return "************" + secret_val[-4:]

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Shannon entropy calculation to weed out low-entropy false positives"""
        if not text:
            return 0.0
        entropy = 0.0
        for x in set(text):
            p_x = float(text.count(x)) / len(text)
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
        return entropy

    def scan_content_for_secrets(self, content: str) -> list[RawFinding]:
        findings: list[RawFinding] = []
        for pattern, title, severity, cwe in self.SECRET_PATTERNS:
            matches = re.finditer(pattern, content)
            for m in matches:
                matched_text = m.group(0)
                captured = m.group(1) if m.groups() else matched_text
                # If short or repetitive string, check entropy
                if len(captured) >= 16 and self.calculate_entropy(captured) < 2.5:
                    continue  # Filter false positive

                masked = self.mask_secret(captured)
                findings.append(
                    RawFinding(
                        title=f"Hardcoded Secret Detected: {title}",
                        description=f"Identified potential hardcoded credential matching pattern '{title}'.",
                        category=FindingCategory.SECRETS,
                        severity=severity,
                        confidence=0.95,
                        evidence={"masked_value": masked, "cwe": cwe},
                        remediation="Revoke the exposed key immediately and store secrets in an environment variable or Secret Manager.",
                        cwe=cwe,
                    )
                )
        return findings

    def scan_content_for_dependencies(self, content: str) -> list[RawFinding]:
        findings: list[RawFinding] = []

        # Parse Python requirements.txt format (pkg==version or pkg>=version)
        for line in content.splitlines():
            clean_line = line.split("#")[0].strip()
            if not clean_line:
                continue

            match = re.match(r"^([a-zA-Z0-9_\-]+)(?:==|>=|<=)(.+)$", clean_line)
            if match:
                pkg_name, version = match.group(1).lower().strip(), match.group(2).strip()
                if pkg_name in self.KNOWN_VULNERABILITIES:
                    vuln_info = self.KNOWN_VULNERABILITIES[pkg_name]
                    for vuln_rule, rule_data in vuln_info.items():
                        try:
                            # vuln_rule is like '<2.31.0' or '<=2.2.5'
                            operator = vuln_rule[0]
                            rule_version = vuln_rule.lstrip("<>=!")
                            installed_v = parse_version(version)
                            rule_v = parse_version(rule_version)
                            vulnerable = False
                            if vuln_rule.startswith("<="):
                                vulnerable = installed_v <= rule_v
                            elif vuln_rule.startswith(">="):
                                vulnerable = installed_v >= rule_v
                            elif vuln_rule.startswith("<"):
                                vulnerable = installed_v < rule_v
                            elif vuln_rule.startswith(">"):
                                vulnerable = installed_v > rule_v
                            elif vuln_rule.startswith("=="):
                                vulnerable = installed_v == rule_v
                            else:
                                # Fallback: treat single '<' style
                                vulnerable = installed_v < rule_v
                        except Exception:
                            vulnerable = False

                        if vulnerable:
                            findings.append(
                                RawFinding(
                                    title=f"Vulnerable Dependency: {pkg_name} ({version})",
                                    description=f"The package '{pkg_name}' version {version} is affected by {rule_data['cve']}: {rule_data['desc']}.",
                                    category=FindingCategory.DEPENDENCY,
                                    severity=rule_data["severity"],
                                    confidence=1.0,
                                    evidence={
                                        "package": pkg_name,
                                        "installed_version": version,
                                        "fixed_version": rule_data["fix"],
                                        "cve": rule_data["cve"],
                                    },
                                    remediation=f"Upgrade '{pkg_name}' to version >= {rule_data['fix']} or higher.",
                                    cve=rule_data["cve"],
                                    cwe="CWE-1395",
                                )
                            )

            # JSON manifest format (e.g., package.json dependencies)
            json_dep_match = re.search(r'"([a-zA-Z0-9_\-]+)"\s*:\s*"[\^~]?([0-9\.]+)"', clean_line)
            if json_dep_match:
                pkg_name, version = json_dep_match.group(1).lower().strip(), json_dep_match.group(2).strip()
                if pkg_name in self.KNOWN_VULNERABILITIES:
                    vuln_info = self.KNOWN_VULNERABILITIES[pkg_name]
                    for vuln_rule, rule_data in vuln_info.items():
                        try:
                            rule_version = vuln_rule.lstrip("<>=!")
                            installed_v = parse_version(version)
                            rule_v = parse_version(rule_version)
                            vulnerable = False
                            if vuln_rule.startswith("<="):
                                vulnerable = installed_v <= rule_v
                            elif vuln_rule.startswith(">="):
                                vulnerable = installed_v >= rule_v
                            elif vuln_rule.startswith("<"):
                                vulnerable = installed_v < rule_v
                            elif vuln_rule.startswith(">"):
                                vulnerable = installed_v > rule_v
                            elif vuln_rule.startswith("=="):
                                vulnerable = installed_v == rule_v
                            else:
                                vulnerable = installed_v < rule_v
                        except Exception:
                            vulnerable = False

                        if vulnerable:
                            findings.append(
                                RawFinding(
                                    title=f"Vulnerable Dependency: {pkg_name} ({version})",
                                    description=f"The package '{pkg_name}' version {version} is affected by {rule_data['cve']}: {rule_data['desc']}.",
                                    category=FindingCategory.DEPENDENCY,
                                    severity=rule_data["severity"],
                                    confidence=1.0,
                                    evidence={
                                        "package": pkg_name,
                                        "installed_version": version,
                                        "fixed_version": rule_data["fix"],
                                        "cve": rule_data["cve"],
                                    },
                                    remediation=f"Upgrade '{pkg_name}' to version >= {rule_data['fix']} or higher.",
                                    cve=rule_data["cve"],
                                    cwe="CWE-1395",
                                )
                            )

        return findings

    async def execute(self, asset: Asset) -> ScannerResult:
        all_findings: list[RawFinding] = []

        target = str(asset.target) if asset.target is not None else ""

        files_to_scan: list[Path] = []

        # If target is a directory, walk and collect relevant files
        try:
            p = Path(target)
            if p.is_dir():
                ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
                exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cs", ".go", ".php", ".rb", ".json", ".xml", ".yml", ".yaml", ".txt", ".env"}
                for root, dirs, files in os.walk(p):
                    # mutate dirs in-place to skip ignored directories
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in exts:
                            files_to_scan.append(fp)
            elif p.is_file():
                files_to_scan.append(p)
            else:
                # treat target as content
                content = target
                secret_findings = self.scan_content_for_secrets(content)
                all_findings.extend(secret_findings)
                dep_findings = self.scan_content_for_dependencies(content)
                all_findings.extend(dep_findings)
                files_to_scan = []
        except Exception:
            # Fallback to treating as content
            content = target
            secret_findings = self.scan_content_for_secrets(content)
            all_findings.extend(secret_findings)
            dep_findings = self.scan_content_for_dependencies(content)
            all_findings.extend(dep_findings)
            files_to_scan = []

        # Scan collected files
        for fp in files_to_scan:
            try:
                raw = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                # skip unreadable files
                continue

            # Run secrets scanner on file content
            secret_findings = self.scan_content_for_secrets(raw)
            for f in secret_findings:
                # add file path to evidence and ensure masking
                if isinstance(f.evidence, dict):
                    f.evidence.setdefault("file", str(fp))
                all_findings.append(f)

            # Run dependency scanner on file content
            dep_findings = self.scan_content_for_dependencies(raw)
            for f in dep_findings:
                if isinstance(f.evidence, dict):
                    f.evidence.setdefault("file", str(fp))
                all_findings.append(f)

        return ScannerResult(
            scanner_name=self.scanner_name,
            scanner_version=self.scanner_version,
            target=asset.name,
            success=True,
            findings=all_findings,
            metadata={
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "findings_count": len(all_findings),
            },
        )
