"""Basic sanity and health check endpoint tests."""

from starlette.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    """Verify the root endpoint returns the default HTML chat interface."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MCP Chat" in response.text


def test_health_check():
    """Verify the health probe returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
