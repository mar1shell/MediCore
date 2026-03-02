"""Integration tests for GET / (health check)."""


def test_health_check_status_ok(client):
    response = client.get("/")
    assert response.status_code == 200


def test_health_check_body(client):
    data = client.get("/").json()
    assert data["status"] == "ok"
    assert data["service"] == "MediCore API"


def test_health_check_content_type(client):
    response = client.get("/")
    assert "application/json" in response.headers["content-type"]
