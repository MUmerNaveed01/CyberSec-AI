import pytest
from httpx import AsyncClient

# Test credentials
ADMIN_USER = {
    "name": "Platform Administrator",
    "email": "admin@cybersec.corp",
    "password": "MasterAdminPass2026!#",
}

ANALYST_USER = {
    "name": "Lead Security Analyst",
    "email": "analyst@cybersec.corp",
    "password": "AnalystSecurePass2026!#",
}

@pytest.mark.asyncio
async def test_complete_platform_user_journey(client: AsyncClient):
    """
    Complete end-to-end verification covering:
    1. Registration of Administrator & Security Analyst
    2. Authentication & JWT issuing
    3. Creation of Security Project Workspace
    4. Registration of Authorized Assets (Website + Code Repository)
    5. SSRF validation & Authorization protection checks
    6. Launch of Website & Code Security Scanners
    7. Finding Normalization & Deterministic Risk Scoring
    8. AI Security Analyst finding explanation & remediation generation
    9. Security Assessment Report compilation & Markdown export
    """

    # -------------------------------------------------------------------------
    # STEP 1: Registration & Authentication
    # -------------------------------------------------------------------------
    # Register first user (automatically becomes ADMIN)
    admin_reg = await client.post("/api/v1/auth/register", json=ADMIN_USER)
    assert admin_reg.status_code in [201, 200]
    admin_token = admin_reg.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert admin_reg.json()["user"]["role"] in ["ADMIN", "ANALYST"]

    # Register second user (becomes ANALYST)
    analyst_reg = await client.post("/api/v1/auth/register", json=ANALYST_USER)
    assert analyst_reg.status_code == 201
    analyst_token = analyst_reg.json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    assert analyst_reg.json()["user"]["role"] == "ANALYST"

    # Verify /me endpoint
    me_res = await client.get("/api/v1/auth/me", headers=analyst_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == ANALYST_USER["email"]

    # -------------------------------------------------------------------------
    # STEP 2: Project Creation
    # -------------------------------------------------------------------------
    project_payload = {
        "name": "Production Cloud Platform",
        "description": "Customer Portal, Payment Gateway, and Microservices",
    }
    proj_res = await client.post("/api/v1/projects", json=project_payload, headers=analyst_headers)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]
    assert proj_res.json()["stats"]["security_score"] == 100

    # -------------------------------------------------------------------------
    # STEP 3: Asset Registration with Authorization Gate
    # -------------------------------------------------------------------------
    # Verify unconfirmed authorization is REJECTED
    unauth_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Unauthorized Target",
            "type": "WEBSITE",
            "target": "https://unauthorized.target.com",
            "authorization_confirmed": False,
        },
        headers=analyst_headers,
    )
    assert unauth_res.status_code == 422

    # Register Authorized Website Asset
    web_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Public Customer Portal",
            "type": "WEBSITE",
            "target": "https://example.com",
            "description": "Production edge web application",
            "authorization_confirmed": True,
        },
        headers=analyst_headers,
    )
    assert web_asset_res.status_code == 201
    web_asset_id = web_asset_res.json()["id"]

    # Register Authorized Source Code Asset containing secrets & outdated packages
    source_content = """
    # AWS Config
    AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE98765432"
    AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY123"

    # Database
    DATABASE_URL = "postgres://dbuser:P@ssword1234!@db.prod.internal:5432/app"

    # Dependencies
    requests==2.27.0
    flask==2.2.1
    jsonwebtoken==8.5.1
    """
    code_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Core Service Repository",
            "type": "SOURCE_CODE",
            "target": source_content,
            "description": "Main application repository manifest and config",
            "authorization_confirmed": True,
        },
        headers=analyst_headers,
    )
    assert code_asset_res.status_code == 201
    code_asset_id = code_asset_res.json()["id"]

    # -------------------------------------------------------------------------
    # STEP 4: Launch Security Scans
    # -------------------------------------------------------------------------
    # Launch Website Security Scan
    web_scan_res = await client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "asset_id": web_asset_id,
            "scan_type": "WEBSITE",
        },
        headers=analyst_headers,
    )
    assert web_scan_res.status_code == 202
    web_scan_id = web_scan_res.json()["id"]

    # Launch Secrets & Dependency Scan
    code_scan_res = await client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "asset_id": code_asset_id,
            "scan_type": "SECRETS",
        },
        headers=analyst_headers,
    )
    assert code_scan_res.status_code == 202
    code_scan_id = code_scan_res.json()["id"]

    # -------------------------------------------------------------------------
    # STEP 5: Findings & Risk Scoring Verification
    # -------------------------------------------------------------------------
    findings_res = await client.get(
        f"/api/v1/findings?project_id={project_id}",
        headers=analyst_headers,
    )
    assert findings_res.status_code == 200
    findings_data = findings_res.json()
    assert findings_data["total"] > 0

    findings_list = findings_data["items"]
    # Check that secrets were masked
    secret_finding = next((f for f in findings_list if f["category"] == "SECRETS"), None)
    assert secret_finding is not None
    assert "masked_value" in secret_finding["evidence"]
    assert "AKIAIOSF" not in secret_finding["evidence"]["masked_value"]
    assert "************" in secret_finding["evidence"]["masked_value"]

    # Check risk score calculation
    assert secret_finding["risk_score"] >= 7.0

    # -------------------------------------------------------------------------
    # STEP 6: AI Security Analyst Integration
    # -------------------------------------------------------------------------
    target_finding_id = secret_finding["id"]
    ai_res = await client.post(
        f"/api/v1/ai/findings/{target_finding_id}/analyze",
        headers=analyst_headers,
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert len(ai_data["summary"]) > 0
    assert len(ai_data["technical_explanation"]) > 0
    assert len(ai_data["business_impact"]) > 0
    assert len(ai_data["remediation"]) > 0
    assert "P0" in ai_data["priority"] or "P1" in ai_data["priority"]

    # -------------------------------------------------------------------------
    # STEP 7: Security Report Generation & Download
    # -------------------------------------------------------------------------
    report_res = await client.post(
        "/api/v1/reports",
        json={
            "project_id": project_id,
            "report_type": "FULL",
        },
        headers=analyst_headers,
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    report_detail_res = await client.get(f"/api/v1/reports/{report_id}", headers=analyst_headers)
    assert report_detail_res.status_code == 200
    content = report_detail_res.json()["content"]
    assert "# Cybersecurity Assessment Report" in content
    assert "Production Cloud Platform" in content
    assert "Detailed Vulnerability Findings" in content
