"""Test auth & rate limit."""
import time
import pytest


def test_register_success(client):
    username = f"testuser_{int(time.time()*1000)}"
    r = client.post("/register", json={
        "username": username,
        "password": "test123456",
        "email": "test@test.com",
    })
    assert r.status_code == 201
    assert r.json()["data"]["username"] == username


def test_register_short_password(client):
    r = client.post("/register", json={
        "username": "shortpw",
        "password": "12",
    })
    assert r.status_code == 422


def test_login_success(client):
    username = f"loginuser_{int(time.time()*1000)}"
    client.post("/register", json={
        "username": username,
        "password": "test123456",
    })
    r = client.post("/login", json={
        "username": username,
        "password": "test123456",
    })
    assert r.status_code == 200
    assert "token" in r.json()["data"]


def test_login_wrong_password(client):
    r = client.post("/login", json={
        "username": "nonexistent_user_xyz",
        "password": "wrong",
    })
    assert r.status_code == 401


def test_get_api_key(client):
    r = client.post("/get-key", json={
        "name": "test-key",
        "rate_limit": 100,
    })
    assert r.status_code == 200
    assert r.json()["data"]["key"].startswith("anw_")


def test_me_anonymous(client):
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is False


def test_me_with_api_key(client):
    r = client.post("/get-key", json={"name": "test-key-2"})
    api_key = r.json()["data"]["key"]
    r = client.get("/me", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is True
    assert r.json()["data"]["method"] == "api_key"


def test_rate_limit_headers(client):
    r = client.get("/share/now")
    assert "X-RateLimit-Limit" in r.headers
    assert "X-RateLimit-Remaining" in r.headers
