"""Health check tests for gateway service."""

from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from mycontextprotocol.gateway import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_endpoint_exists(client: TestClient) -> None:
    """Test that health endpoint exists and returns 200."""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK


def test_health_endpoint_response_format(client: TestClient) -> None:
    """Test health endpoint returns proper JSON format."""
    response = client.get("/health")
    assert response.status_code in [
        HTTPStatus.OK,
        HTTPStatus.SERVICE_UNAVAILABLE,
    ]  # 503 if deps unavailable
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "checks" in data
    assert data["status"] in ["pass", "warn", "fail"]


def test_gateway_endpoints_exist(client: TestClient) -> None:
    """Test that all gateway endpoints are registered."""
    # Check OpenAPI schema for endpoint definitions
    response = client.get("/openapi.json")
    assert response.status_code == HTTPStatus.OK

    schema = response.json()
    paths = schema.get("paths", {})

    # Verify required endpoints exist
    assert "/context/state" in paths
    assert "/context/query/documents" in paths
    assert "/context/query/graph" in paths
    assert "/ingest" in paths


@patch("mycontextprotocol.gateway.get_user_state")
def test_context_state_endpoint_structure(mock_get_state: Mock, client: TestClient) -> None:
    """Test context/state endpoint accepts proper request structure."""
    mock_get_state.return_value = {"memories": [], "user_id": "test-user"}

    response = client.post("/context/state", json={"user_id": "test-user"})

    # Should not return 422 (validation error)
    assert response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY


@patch("mycontextprotocol.gateway.query_documents")
def test_query_documents_endpoint_structure(mock_query: Mock, client: TestClient) -> None:
    """Test context/query/documents endpoint accepts proper request structure."""
    mock_query.return_value = []

    response = client.post("/context/query/documents", json={"query": "test query", "top_k": 5})

    # Should not return 422 (validation error)
    assert response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY


@patch("mycontextprotocol.gateway.query_graph")
def test_query_graph_endpoint_structure(mock_query: Mock, client: TestClient) -> None:
    """Test context/query/graph endpoint accepts proper request structure."""
    mock_query.return_value = {"nodes": [], "edges": []}

    response = client.post("/context/query/graph", json={"query": "test query", "mode": "local"})

    # Should not return 422 (validation error)
    assert response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY


@patch("mycontextprotocol.gateway.app")
def test_ingest_endpoint_structure(mock_app: Mock, client: TestClient) -> None:
    """Test ingest endpoint accepts proper request structure."""
    # Mock the app.state.redis
    mock_redis = Mock()
    mock_redis.lpush = Mock(return_value=1)
    mock_app.state.redis = mock_redis

    # Patch at the gateway module level
    with patch("mycontextprotocol.gateway.app.state") as mock_state:
        mock_state.redis = mock_redis

        response = client.post(
            "/ingest",
            json={
                "content": "test content",
                "metadata": {"source": "test"},
                "user_id": "test-user",
            },
        )

    # Should not return 422 (validation error)
    assert response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY
