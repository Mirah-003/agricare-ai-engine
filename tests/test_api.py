"""Integration tests for FastAPI endpoints and security validation."""
import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Client fixture triggering FastAPI lifespan events."""
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Agricare AI API is running" in response.json()["message"]


def test_generate_content_unauthorized(client):
    response = client.post("/generateContent", json={"query": "My chickens are coughing."})
    assert response.status_code == 403
    assert "Could not validate credentials" in response.json()["detail"]


def test_generate_content_with_header_key(client):
    headers = {"X-API-Key": "agricare_test_key_123"}
    response = client.post("/generateContent", headers=headers, json={"query": "My chickens are coughing."})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "status" in data
    assert "urgency" in data


def test_generate_content_with_query_param_key(client):
    response = client.post(
        "/generateContent?key=agricare_test_key_123",
        json={"query": "My chickens have bloody droppings and weight loss."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "fallback"]
    assert data["urgency"] in ["RED", "ORANGE", "YELLOW", "GREEN"]
