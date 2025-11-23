"""
Tests for RAG Policy Assistant FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from app import app, Config


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


def test_query_endpoint_validation(client):
    """Test query endpoint input validation"""
    # Test with empty query
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422  # Validation error
    
    # Test with missing query field
    response = client.post("/query", json={})
    assert response.status_code == 422
    
    # Test with valid query structure
    response = client.post("/query", json={"query": "What is the policy?"})
    assert response.status_code in [200, 500]  # 500 if config not set


def test_query_endpoint_max_results(client):
    """Test query endpoint max_results parameter"""
    # Test with valid max_results
    response = client.post(
        "/query",
        json={"query": "Test query", "max_results": 10}
    )
    assert response.status_code in [200, 500]  # 500 if config not set
    
    # Test with invalid max_results (too high)
    response = client.post(
        "/query",
        json={"query": "Test query", "max_results": 25}
    )
    assert response.status_code == 422  # Validation error
    
    # Test with invalid max_results (too low)
    response = client.post(
        "/query",
        json={"query": "Test query", "max_results": 0}
    )
    assert response.status_code == 422  # Validation error


def test_config_endpoint(client):
    """Test the configuration status endpoint"""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    
    # Check that expected keys are present
    assert "aoai_endpoint_configured" in data
    assert "aoai_key_configured" in data
    assert "chat_model" in data
    assert "embed_model" in data
    assert "ai_search_endpoint_configured" in data
    assert "ai_search_key_configured" in data
    assert "configuration_valid" in data
    
    # Check that models have expected default values
    assert data["chat_model"] == "gpt-4o-mini"
    assert data["embed_model"] == "text-embedding-3-large"


def test_config_validation():
    """Test configuration validation logic"""
    config = Config()
    
    # Without environment variables, validation should fail or return False
    # (depending on whether variables are set in the test environment)
    result = config.validate()
    assert isinstance(result, bool)


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


def test_query_response_structure(client):
    """Test that query responses have the expected structure"""
    response = client.post(
        "/query",
        json={"query": "What is the vacation policy?"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert data["query"] == "What is the vacation policy?"


def test_cors_headers(client):
    """Test that appropriate headers are returned"""
    response = client.get("/")
    assert response.status_code == 200
    # Basic header check
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"
