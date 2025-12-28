import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    """Başarılı kullanıcı kaydı."""
    user_data = {"name": "Test User", "email": "test@example.com"}
    
    # Await the request
    response = await client.post("/users/", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    """Aynı email ile kayıt engellenmeli."""
    user_data = {"name": "Duplicate", "email": "dup@example.com"}
    
    # First creation
    await client.post("/users/", json=user_data)
    
    # Second creation (Duplicate)
    response = await client.post("/users/", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Kullanıcı listeleme."""
    await client.post("/users/", json={"name": "U1", "email": "u1@test.com"})
    await client.post("/users/", json={"name": "U2", "email": "u2@test.com"})
    
    response = await client.get("/users/")
    
    assert response.status_code == 200
    assert len(response.json()) >= 2