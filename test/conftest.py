"""Pytest configuration and shared fixtures for MCP Chat and Database Agent tests."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture for endpoint integration testing."""
    with TestClient(app) as c:
        yield c
