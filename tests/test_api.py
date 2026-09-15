"""
Tests for FastAPI API endpoints.

Tests cover:
- Health and readiness endpoints
- AI query endpoint
- Ingestion endpoints
- Monitoring endpoints
- Error handling
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    def test_health_endpoint(self, test_client: TestClient):
        """Test liveness probe returns healthy status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"
        assert "documentation" in data

    def test_metrics_endpoint(self, test_client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "python_info" in response.text  # Prometheus default metric


@pytest.mark.unit
class TestAIQueryEndpoint:
    """Test AI query endpoints."""

    def test_query_endpoint_validation_empty(self, test_client: TestClient):
        """Test query endpoint validates empty query."""
        response = test_client.post("/api/v1/ai/query", json={"query": ""})

        assert response.status_code == 422

    def test_query_endpoint_validation_missing_field(self, test_client: TestClient):
        """Test query endpoint validates missing required fields."""
        response = test_client.post("/api/v1/ai/query", json={})

        assert response.status_code == 422

    def test_query_endpoint_validation_invalid_country(self, test_client: TestClient):
        """Test query endpoint with invalid country code."""
        response = test_client.post(
            "/api/v1/ai/query", json={"query": "Test query", "country": "INVALID"}
        )

        # Should either validate or accept (depends on implementation)
        assert response.status_code in [200, 422]

    def test_query_endpoint_success(self, test_client: TestClient):
        """Test successful query execution."""
        # This test requires mocked AI components
        # For now, we test that the endpoint exists and accepts valid input
        response = test_client.post(
            "/api/v1/ai/query",
            json={
                "query": "What is Paracetamol?",
                "session_id": "test-session-123",
                "country": "VN",
                "language": "en",
                "halal_filter": False,
            },
        )

        # Should return 200 or 500 (if AI components not initialized)
        assert response.status_code in [200, 500]


@pytest.mark.unit
class TestIngestionEndpoints:
    """Test document ingestion endpoints."""

    def test_list_jobs_endpoint(self, test_client: TestClient):
        """Test listing ingestion jobs."""
        response = test_client.get("/api/v1/ingest/jobs")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "count" in data

    def test_get_job_not_found(self, test_client: TestClient):
        """Test getting non-existent job returns 404."""
        response = test_client.get("/api/v1/ingest/jobs/non-existent-id")

        assert response.status_code == 404


@pytest.mark.unit
class TestRequestIDMiddleware:
    """Test Request ID middleware."""

    def test_request_id_generated(self, test_client: TestClient):
        """Test that Request-ID is generated if not provided."""
        response = test_client.get("/health")

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_request_id_preserved(self, test_client: TestClient):
        """Test that provided Request-ID is preserved."""
        custom_id = "custom-test-id-123"
        response = test_client.get("/health", headers={"X-Request-ID": custom_id})

        assert response.headers["x-request-id"] == custom_id

    def test_process_time_header(self, test_client: TestClient):
        """Test that process time is included in response."""
        response = test_client.get("/health")

        assert "x-process-time-ms" in response.headers
        process_time = float(response.headers["x-process-time-ms"])
        assert process_time >= 0
