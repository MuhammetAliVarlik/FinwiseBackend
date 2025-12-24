from fastapi.testclient import TestClient
from app.schemas.user import UserCreate

def test_create_user_success(client: TestClient):
    """Başarılı kullanıcı kaydı."""
    user_data = {"name": "Test User", "email": "test@example.com"}
    response = client.post("/users/", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_user_duplicate_email(client: TestClient):
    """Aynı email ile kayıt engellenmeli."""
    user_data = {"name": "Duplicate", "email": "dup@example.com"}
    
    client.post("/users/", json=user_data)
    
    response = client.post("/users/", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_list_users(client: TestClient):
    """Kullanıcı listeleme."""
    client.post("/users/", json={"name": "U1", "email": "u1@test.com"})
    client.post("/users/", json={"name": "U2", "email": "u2@test.com"})
    
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) >= 2