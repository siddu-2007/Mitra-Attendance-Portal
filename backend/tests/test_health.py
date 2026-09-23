"""Test health check and API documentation endpoints."""

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "html" in response.headers.get("content-type", "")


def test_redoc_available(client):
    response = client.get("/redoc")
    assert response.status_code == 200
