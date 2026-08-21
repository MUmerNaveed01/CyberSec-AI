import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "project_owner@cybersec.io") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={"name": "Project Owner", "email": email, "password": "StrongPassword123!"},
    )
    if res.status_code == 201:
        return res.json()["access_token"]
    # If already exists, login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    return login_res.json()["access_token"]

@pytest.mark.asyncio
async def test_project_crud_lifecycle(client: AsyncClient):
    token = await get_auth_token(client, "project_tester@cybersec.io")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "E-Commerce Gateway", "description": "Core payments and store"},
        headers=headers,
    )
    assert create_res.status_code == 201
    project_data = create_res.json()
    project_id = project_data["id"]
    assert project_data["name"] == "E-Commerce Gateway"
    assert project_data["stats"]["security_score"] == 100

    # 2. List Projects
    list_res = await client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 3. Get Project Detail
    get_res = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 4. Update Project
    update_res = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "E-Commerce Gateway v2"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "E-Commerce Gateway v2"

    # 5. Delete Project
    del_res = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_res.status_code == 204

@pytest.mark.asyncio
async def test_asset_registration_and_authorization_check(client: AsyncClient):
    token = await get_auth_token(client, "asset_tester@cybersec.io")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project first
    proj_res = await client.post(
        "/api/v1/projects",
        json={"name": "Asset Test Project"},
        headers=headers,
    )
    project_id = proj_res.json()["id"]

    # 1. Attempt registering asset WITHOUT authorization confirmation -> MUST FAIL
    unauth_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Unauthorized Domain",
            "type": "WEBSITE",
            "target": "https://example.com",
            "authorization_confirmed": False,
        },
        headers=headers,
    )
    assert unauth_asset_res.status_code == 422

    # 2. Register authorized asset -> MUST SUCCEED
    auth_asset_res = await client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Production Web App",
            "type": "WEBSITE",
            "target": "https://secure-app.internal.io",
            "authorization_confirmed": True,
        },
        headers=headers,
    )
    assert auth_asset_res.status_code == 201
    asset_data = auth_asset_res.json()
    assert asset_data["authorization_confirmed"] is True
    assert asset_data["type"] == "WEBSITE"

    # 3. List assets under project
    assets_list = await client.get(f"/api/v1/projects/{project_id}/assets", headers=headers)
    assert assets_list.status_code == 200
    assert assets_list.json()["total"] == 1
