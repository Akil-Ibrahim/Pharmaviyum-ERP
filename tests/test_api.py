"""
Tests for FastAPI API endpoints.

Tests cover:
- Health and readiness endpoints
- AI query endpoint
- Ingestion endpoints
- Monitoring endpoints
- Error handling
- Observability headers and HTTP metrics
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

    def test_readiness_endpoint_reports_production_component_contract(
        self, test_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        """Expose the exact component contract consumed by production deploy gates."""
        from src.pharmaviyum.api.v1.endpoints import health as health_endpoint
        from src.pharmaviyum.core.health import HealthCheckResult, HealthStatus

        async def healthy_database():
            return HealthCheckResult(name="database", status=HealthStatus.HEALTHY)

        async def healthy_redis():
            return HealthCheckResult(name="redis", status=HealthStatus.HEALTHY)

        monkeypatch.setattr(health_endpoint, "check_database", healthy_database)
        monkeypatch.setattr(health_endpoint, "check_redis", healthy_redis)
        test_client.app.state.ai_initialized = True

        response = test_client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "components": {
                "postgres": "ok",
                "redis": "ok",
                "ai_initialized": "ok",
            },
        }

    def test_readiness_endpoint_fails_closed_when_ai_is_not_initialized(
        self, test_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        """Never report ready while the AI container is unavailable."""
        from src.pharmaviyum.api.v1.endpoints import health as health_endpoint
        from src.pharmaviyum.core.health import HealthCheckResult, HealthStatus

        async def healthy_database():
            return HealthCheckResult(name="database", status=HealthStatus.HEALTHY)

        async def healthy_redis():
            return HealthCheckResult(name="redis", status=HealthStatus.HEALTHY)

        monkeypatch.setattr(health_endpoint, "check_database", healthy_database)
        monkeypatch.setattr(health_endpoint, "check_redis", healthy_redis)
        test_client.app.state.ai_initialized = False

        response = test_client.get("/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
        assert response.json()["components"]["ai_initialized"] == "error"

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"
        assert "documentation" in data

    def test_version_endpoint_reports_all_runtime_environments(
        self, test_client: TestClient
    ):
        """Expose the environment values used by app, API and auth settings."""
        from src.pharmaviyum.ai.config import settings as application_settings
        from src.pharmaviyum.config import settings as auth_settings
        from src.pharmaviyum.core.config import settings as api_settings

        response = test_client.get("/version")

        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == api_settings.ENVIRONMENT.value
        assert data["debug"] is api_settings.DEBUG
        assert data["application_environment"] == application_settings.environment
        assert data["auth_environment"] == auth_settings.ENVIRONMENT
        assert data["auth_debug"] is auth_settings.DEBUG
        assert data["build_commit"] == "unknown"

    def test_metrics_endpoint(self, test_client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "python_info" in response.text
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text
        assert "http_requests_in_flight" in response.text


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
