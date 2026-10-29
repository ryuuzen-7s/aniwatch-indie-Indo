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


class TestMethodRestrictor:
    @pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH"])
    def test_method_not_allowed_share(self, client, method):
        r = client.request(method, "/share/now")
        assert r.status_code == 405
        data = r.json()
        assert data["success"] is False
        assert data["error"]["code"] == "HTTP_405"

    @pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH"])
    def test_method_not_allowed_health(self, client, method):
        r = client.request(method, "/health")
        assert r.status_code == 405

    def test_allow_header(self, client):
        r = client.put("/share/now")
        assert r.status_code == 405
        allow = r.headers.get("allow", "")
        assert "GET" in allow
        assert "POST" in allow

    def test_get_still_works(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_options_allowed(self, client):
        """OPTIONS harus lolos (CORS preflight)."""
        r = client.options(
            "/share/now", 
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert r.status_code in (200, 204)

    def test_excluded_path_delete(self, client):
        r = client.delete("/keys/999")
        assert r.status_code != 405
        assert r.status_code in (401, 403, 404)

    def test_docs_accessible(self, client):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_accessible(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200

    def test_share_post_allowed(self, client):
        r = client.post(
            "/share/linkask/nonexistent-slug-xyz",
            json={"type": "all", "deep": False},
        )
        assert r.status_code != 405