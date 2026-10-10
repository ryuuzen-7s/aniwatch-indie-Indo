"""Test API endpoints."""
import pytest


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_stats(client):
    r = client.get("/stats")
    assert r.status_code == 200
    assert "counts" in r.json()["data"]


def test_404_format(client):
    r = client.get("/tidak-ada-endpoint")
    assert r.status_code == 404
    data = r.json()
    assert data["success"] is False
    assert data["error"] is not None
