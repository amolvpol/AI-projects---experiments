"""
Tests for RAG Policy Assistant FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "RAG Policy Assistant" in data["message"]


def test_upload_policy_invalid_file(client):
    """Test upload with invalid file type"""
    response = client.post("/upload-policy", files={"file": ("test.txt", b"content", "text/plain")})
    assert response.status_code == 400


def test_ask_policy_validation(client):
    """Test ask endpoint input validation"""
    # Test with empty question
    response = client.post("/ask-policy", json={"question": ""})
    assert response.status_code == 422  # Validation error
    
    # Test with missing question field
    response = client.post("/ask-policy", json={})
    assert response.status_code == 422


def test_api_docs_available(client):
    """Test that API documentation is accessible"""
    # Test Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200
    
    # Test OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "RAG Policy Assistant"


def test_cors_headers(client):
    """Test that appropriate headers are returned"""
    response = client.get("/")
    assert response.status_code == 200
    # Basic header check
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"
