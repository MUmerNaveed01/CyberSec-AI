import pytest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "name": "Security Analyst",
    "email": "analyst@cybersec.io",
    "password": "StrongPassword123!",
}

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "analyst@cybersec.io"
    # First registered user must be ADMIN
    assert data["user"]["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # Attempt register again with same email
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "CONFLICT"

@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    weak_payload = {
        "name": "Weak User",
        "email": "weak@cybersec.io",
        "password": "weak",  # too short, no uppercase, no numbers, no special chars
    }
    response = await client.post("/api/v1/auth/register", json=weak_payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@cybersec.io", "password": "StrongPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@cybersec.io", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_get_me_flow(client: AsyncClient):
    # Login first
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@cybersec.io", "password": "StrongPassword123!"},
    )
    token = login_res.json()["access_token"]

    # Call /me with bearer token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "analyst@cybersec.io"

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@cybersec.io", "password": "StrongPassword123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
