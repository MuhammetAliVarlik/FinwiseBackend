# app/tests/test_users.py
from app.schemas.user import UserCreate

def test_create_user(client):
    payload = {"name": "Alice", "email": "alice@example.com"}
    response = client.post("/users/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"

def test_list_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
