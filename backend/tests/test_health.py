from fastapi.testclient import TestClient


def test_health_root_endpoint(client: TestClient):
    """Verify that GET /health returns 200 OK and expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


def test_api_health_endpoint(client: TestClient):
    """Verify that GET /api/health (used by frontend) returns 200 OK and expected status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
