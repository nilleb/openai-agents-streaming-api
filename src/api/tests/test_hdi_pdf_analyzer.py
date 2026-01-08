"""Tests for the HDI PDF Analyzer API router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ..main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHDIPDFAnalyzerInfo:
    """Tests for the /hdi-pdf-analyzer/info endpoint."""

    def test_info_endpoint_returns_agent_info(self, client):
        """Test that info endpoint returns agent information."""
        response = client.get("/hdi-pdf-analyzer/info")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "HDI PDF Analyzer"
        assert "agent_name" in data
        assert "instructions" in data
        assert "model" in data
        assert "endpoints" in data
        assert "session_config" in data

    def test_info_endpoint_includes_correct_endpoints(self, client):
        """Test that info endpoint lists all available endpoints."""
        response = client.get("/hdi-pdf-analyzer/info")

        assert response.status_code == 200
        data = response.json()

        endpoints = data["endpoints"]
        assert "/hdi-pdf-analyzer/run" in endpoints.values()
        assert "/hdi-pdf-analyzer/stream" in endpoints.values()
        assert "/hdi-pdf-analyzer/info" in endpoints.values()

    def test_info_shows_subagent_tools(self, client):
        """Test that the agent has sub-agent tools configured."""
        response = client.get("/hdi-pdf-analyzer/info")

        assert response.status_code == 200
        data = response.json()

        # HDI PDF Analyzer should have sub-agents as tools
        assert data["tools_count"] >= 3  # pdf-extractor, gii-extractor, data-aggregator


class TestHDIPDFAnalyzerRun:
    """Tests for the /hdi-pdf-analyzer/run endpoint."""

    def test_run_endpoint_accepts_valid_request(self, client):
        """Test that run endpoint accepts a valid request structure."""
        with patch("agents.Runner.run", new_callable=AsyncMock) as mock_run:
            # Mock the result
            mock_result = MagicMock()
            mock_result.final_output = "Test analysis result"
            mock_result.context_wrapper = MagicMock()
            mock_result.context_wrapper.usage = None
            mock_result.raw_responses = []
            mock_run.return_value = mock_result

            response = client.post(
                "/hdi-pdf-analyzer/run",
                json={"input": "Analyze the HDI report"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "final_output" in data
            assert "success" in data

    def test_run_endpoint_with_session_id(self, client):
        """Test that run endpoint accepts session_id for conversation memory."""
        with patch("agents.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_result = MagicMock()
            mock_result.final_output = "Test analysis result"
            mock_result.context_wrapper = MagicMock()
            mock_result.context_wrapper.usage = None
            mock_result.raw_responses = []
            mock_run.return_value = mock_result

            response = client.post(
                "/hdi-pdf-analyzer/run",
                json={
                    "input": "Analyze the HDI report",
                    "session_id": "test-session-123",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("session_id") == "test-session-123"


class TestHDIPDFAnalyzerStream:
    """Tests for the /hdi-pdf-analyzer/stream endpoint."""

    def test_stream_endpoint_returns_event_stream(self, client):
        """Test that stream endpoint returns an event stream."""
        with patch("agents.Runner.run_streamed") as mock_run_streamed:
            # Mock the streaming result
            mock_stream_result = MagicMock()
            mock_stream_result.final_output = "Streamed analysis result"
            mock_stream_result.current_turn = 1

            async def mock_stream_events():
                return
                yield  # Make it an async generator

            mock_stream_result.stream_events = mock_stream_events
            mock_run_streamed.return_value = mock_stream_result

            response = client.post(
                "/hdi-pdf-analyzer/stream",
                json={"input": "Analyze the HDI report"},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


class TestHDIPDFAnalyzerSession:
    """Tests for session-related endpoints."""

    def test_get_session_messages_returns_response(self, client):
        """Test that get session messages endpoint returns a valid response."""
        response = client.get("/hdi-pdf-analyzer/session/test-session-id")

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "messages" in data
        assert "message_count" in data

    def test_clear_session_returns_response(self, client):
        """Test that clear session endpoint returns a valid response."""
        response = client.delete("/hdi-pdf-analyzer/session/test-session-id")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data


class TestHDIPDFAnalyzerRouterConfiguration:
    """Tests for the router configuration."""

    def test_router_has_correct_prefix(self, client):
        """Test that all endpoints have the correct prefix."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        paths = schema.get("paths", {})

        # Check that HDI PDF analyzer paths exist
        assert "/hdi-pdf-analyzer/run" in paths
        assert "/hdi-pdf-analyzer/stream" in paths
        assert "/hdi-pdf-analyzer/info" in paths

    def test_router_included_in_app(self, client):
        """Test that the HDI PDF analyzer router is included in the app."""
        response = client.get("/")

        assert response.status_code == 200
        # The app should be running and responding


class TestHDIPDFAnalyzerAgentLoading:
    """Tests for agent loading functionality."""

    def test_agent_has_correct_name(self):
        """Test that the loaded agent has the correct name."""
        from ..routers.hdi_pdf_analyzer import hdi_analyzer_agent

        # The agent name should match what's in agents.yaml
        assert hdi_analyzer_agent.name == "Hdi Pdf Analyzer"

    def test_agent_has_sub_agent_tools(self):
        """Test that the agent has sub-agent tools."""
        from ..routers.hdi_pdf_analyzer import hdi_analyzer_agent

        # Should have tools for sub-agents
        assert len(hdi_analyzer_agent.tools) >= 3

        tool_names = [t.name for t in hdi_analyzer_agent.tools]
        assert "pdf_extractor" in tool_names
        assert "gii_extractor" in tool_names
        assert "data_aggregator" in tool_names

    def test_agent_has_instructions(self):
        """Test that the agent has instructions loaded from skill."""
        from ..routers.hdi_pdf_analyzer import hdi_analyzer_agent

        assert hdi_analyzer_agent.instructions is not None
        assert isinstance(hdi_analyzer_agent.instructions, str)
        assert len(hdi_analyzer_agent.instructions) > 0

        # Should contain HDI/GII related content
        assert (
            "GII" in hdi_analyzer_agent.instructions
            or "HDI" in hdi_analyzer_agent.instructions
        )
