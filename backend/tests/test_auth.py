import pytest
from backend.app.auth import get_password_hash, verify_password, create_access_token
from backend.app.models import UserRole

def test_password_hashing():
    raw = "MySecurePassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation():
    token = create_access_token({"sub": "test@questforge.io", "role": "admin"})
    assert isinstance(token, str)
    assert len(token) > 20

def test_login_api_success(client):
    res = client.post("/auth/login", json={
        "email": "admin@questforge.io",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == UserRole.ADMIN.value
    assert data["token_type"] == "bearer"

def test_login_api_invalid_password(client):
    res = client.post("/auth/login", json={
        "email": "admin@questforge.io",
        "password": "wrong-password"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_login_api_nonexistent_user(client):
    res = client.post("/auth/login", json={
        "email": "doesnotexist@questforge.io",
        "password": "password"
    })
    assert res.status_code == 401

def test_get_me_authenticated(client, auth_headers):
    res = client.get("/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "reviewer@questforge.io"
    assert data["role"] == UserRole.REVIEWER.value

def test_get_me_unauthorized(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
