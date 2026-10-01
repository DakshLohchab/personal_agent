from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "life-sandbox-api",
        "version": "0.1.0",
    }
