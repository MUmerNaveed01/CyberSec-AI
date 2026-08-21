import pytest
from httpx import AsyncClient

async def get_token(client: AsyncClient) -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={"name": "End2End Tester", "email": "e2e@cybersec.io", "password": "StrongPassword123!"},
    )
    if res.status_code == 201:
        return res.json()["access_token"]
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "e2e@cybersec.io", "password": "StrongPassword123!"},
    )
    return login_res.json()["access_token"]

@pytest.mark.asyncio
async def test_full_platform_scanning_and_findings_pipeline(client: AsyncClient):
    token = await get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Security Project
    proj_res = await client.post(
        "/api/v1/projects",
        json={"name": "Pipeline Target System", "description": "Core assessment scope"},
        headers=headers,
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Register Authorized Website Asset
    web_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Target Portal",
            "type": "WEBSITE",
            "target": "https://example.com",
            "authorization_confirmed": True,
        },
        headers=headers,
    )
    assert web_asset_res.status_code == 201
    web_asset_id = web_asset_res.json()["id"]

    # 3. Register Code Asset with Hardcoded Secret & Vulnerable Dependency
    code_content = """
    AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE12345678"
    DATABASE_URL = "postgres://admin:SuperSecretPass123@db.internal:5432/app"
    requests==2.28.0
    flask==2.2.0
    """
    code_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "API Service Manifest",
            "type": "SOURCE_CODE",
            "target": code_content,
            "authorization_confirmed": True,
        },
        headers=headers,
    )
    assert code_asset_res.status_code == 201
    code_asset_id = code_asset_res.json()["id"]

    # 4. Launch Secrets & Dependency Scan
    scan_res = await client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "asset_id": code_asset_id,
            "scan_type": "SECRETS",
        },
        headers=headers,
    )
    assert scan_res.status_code == 202
    scan_id = scan_res.json()["id"]

    # 5. Verify Findings generated
    findings_res = await client.get(
        f"/api/v1/findings?project_id={project_id}",
        headers=headers,
    )
    assert findings_res.status_code == 200
    findings_data = findings_res.json()
    assert findings_data["total"] >= 1

    first_finding = findings_data["items"][0]
    finding_id = first_finding["id"]
    assert first_finding["risk_score"] > 0

    # 6. Generate AI Security Analysis
    ai_res = await client.post(
        f"/api/v1/ai/findings/{finding_id}/analyze",
        headers=headers,
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "technical_explanation" in ai_data
    assert "business_impact" in ai_data
    assert "remediation" in ai_data

    # 7. Generate Security Assessment Report
    report_res = await client.post(
        "/api/v1/reports",
        json={
            "project_id": project_id,
            "report_type": "FULL",
        },
        headers=headers,
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    # 8. View Report Content
    report_view_res = await client.get(
        f"/api/v1/reports/{report_id}",
        headers=headers,
    )
    assert report_view_res.status_code == 200
    assert "Cybersecurity Assessment Report" in report_view_res.json()["content"]
