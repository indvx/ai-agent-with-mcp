"""Pytest configuration and shared fixtures for MCP Chat application."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture for endpoint testing."""
    with TestClient(app) as c:
        yield c
