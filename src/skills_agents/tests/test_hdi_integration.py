"""
Integration tests for HDI PDF Analyzer that call OpenAI API.

These tests require:
- OPENAI_API_KEY environment variable
- Network access to OpenAI API

Run with: ./cli integration
Excluded from regular test suite.
"""

import json
import logging
import os
from pathlib import Path

import pytest

from agents import Runner

from ..loader import load_top_level_agents
from ..schemas.hdi_pdf_analyzer import (
    HDIPDFAnalysisResult,
)


logger = logging.getLogger(__name__)

# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - skipping integration tests",
)

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
SAMPLE_PDF_URL = "https://hdr.undp.org/system/files/documents/global-report-document/hdr2023-24reporten.pdf"


class TestHDIAnalyzerIntegration:
    """Integration tests for the HDI PDF Analyzer agent."""

    @pytest.fixture
    def agents(self) -> dict:
        """Load all configured agents."""
        config_path = EXAMPLES_DIR / "agents.yaml"
        return load_top_level_agents(config_path)

    @pytest.fixture
    def hdi_analyzer(self, agents):
        """Get the HDI PDF Analyzer agent."""
        return agents.get("HDI PDF Analyzer")

    @pytest.mark.asyncio
    async def test_hdi_analyzer_responds(self, hdi_analyzer):
        """Test that HDI analyzer agent responds to a basic query."""
        assert hdi_analyzer is not None

        result = await Runner.run(
            starting_agent=hdi_analyzer,
            input=f"Analyze the GII data from the HDR 2023-24 report at {SAMPLE_PDF_URL}. "
            "Extract the table of contents, find the Gender Inequality Index statistics, "
            "and compute the average GII for European countries. "
            "Return the result as structured JSON.",
        )

        assert result.final_output is not None
        logger.info(f"Agent response length: {len(result.final_output)}")

    @pytest.mark.asyncio
    async def test_hdi_analyzer_extracts_gii_data(self, hdi_analyzer):
        """Test that HDI analyzer extracts GII data correctly."""
        assert hdi_analyzer is not None

        result = await Runner.run(
            starting_agent=hdi_analyzer,
            input=f"""Analyze the Gender Inequality Index data from:
{SAMPLE_PDF_URL}

Focus specifically on extracting:
1. GII values for European countries
2. The average GII for Europe

Return ONLY a JSON object with this structure:
{{
  "european_countries": [
    {{"name": "Country", "gii_value": 0.123}}
  ],
  "average_gii": 0.123,
  "countries_count": 40
}}""",
        )

        output = result.final_output
        assert output is not None
        logger.info(f"GII extraction result: {output[:500]}...")

        # Try to parse as JSON
        # The output might have markdown code blocks, so try to extract JSON
        json_str = output
        if "```json" in output:
            start = output.find("```json") + 7
            end = output.find("```", start)
            json_str = output[start:end].strip()
        elif "```" in output:
            start = output.find("```") + 3
            end = output.find("```", start)
            json_str = output[start:end].strip()

        try:
            data = json.loads(json_str)
            assert "european_countries" in data or "average_gii" in data
            logger.info(f"Successfully parsed JSON with keys: {data.keys()}")
        except json.JSONDecodeError:
            logger.warning("Could not parse response as JSON - checking for key data")
            # At minimum, response should mention European countries
            assert any(
                country.lower() in output.lower()
                for country in ["denmark", "sweden", "germany", "france"]
            )

    @pytest.mark.asyncio
    async def test_hdi_analyzer_identifies_top_countries(self, hdi_analyzer):
        """Test that HDI analyzer identifies top-performing countries."""
        assert hdi_analyzer is not None

        result = await Runner.run(
            starting_agent=hdi_analyzer,
            input=f"""From the HDR 2023-24 report ({SAMPLE_PDF_URL}), 
identify the top 5 countries with the LOWEST Gender Inequality Index (best performers).

Return the answer as a simple list with country names and GII values.""",
        )

        output = result.final_output
        assert output is not None

        # Top performers should include Nordic countries
        output_lower = output.lower()
        top_performers = ["denmark", "switzerland", "sweden", "belgium", "netherlands"]
        found_count = sum(1 for c in top_performers if c in output_lower)

        assert found_count >= 3, (
            f"Expected at least 3 top performers, found {found_count}"
        )
        logger.info(f"Found {found_count}/5 expected top performers in response")


class TestGIIExtractorIntegration:
    """Integration tests for the GII Extractor sub-agent."""

    @pytest.fixture
    def agents(self) -> dict:
        """Load all configured agents."""
        config_path = EXAMPLES_DIR / "agents.yaml"
        return load_top_level_agents(config_path)

    @pytest.fixture
    def gii_extractor(self, agents):
        """Get the GII Extractor agent."""
        return agents.get("GII Extractor")

    @pytest.mark.asyncio
    async def test_gii_extractor_understands_gii(self, gii_extractor):
        """Test that GII extractor understands the Gender Inequality Index."""
        assert gii_extractor is not None

        result = await Runner.run(
            starting_agent=gii_extractor,
            input="What is the Gender Inequality Index and what are its components?",
        )

        output = result.final_output
        assert output is not None

        # Should mention key GII components
        output_lower = output.lower()
        components = ["reproductive health", "empowerment", "labor"]
        found = sum(1 for c in components if c in output_lower)
        assert found >= 2, "Expected at least 2 GII components mentioned"


class TestDataAggregatorIntegration:
    """Integration tests for the Data Aggregator sub-agent."""

    @pytest.fixture
    def agents(self) -> dict:
        """Load all configured agents."""
        config_path = EXAMPLES_DIR / "agents.yaml"
        return load_top_level_agents(config_path)

    @pytest.fixture
    def data_aggregator(self, agents):
        """Get the Data Aggregator agent."""
        return agents.get("Data Aggregator")

    @pytest.mark.asyncio
    async def test_data_aggregator_computes_average(self, data_aggregator):
        """Test that data aggregator can compute averages."""
        assert data_aggregator is not None

        result = await Runner.run(
            starting_agent=data_aggregator,
            input="""Compute the average of these GII values for European countries:
- Denmark: 0.013
- Sweden: 0.023
- Norway: 0.026
- Finland: 0.033
- Germany: 0.072

Return the average and identify the min/max countries.""",
        )

        output = result.final_output
        assert output is not None

        # Should identify Denmark as min
        assert "denmark" in output.lower()
        # Should compute reasonable average (around 0.033)
        assert "0.03" in output or "0.04" in output


class TestIntegrationResultValidation:
    """Tests for validating integration test results against expected schema."""

    def test_sample_result_validates(self):
        """Test that a sample result validates against the schema."""
        # This test doesn't call OpenAI - it just validates the schema works
        from ..schemas.hdi_pdf_analyzer import (
            DocumentInfo,
            EuropeanAnalysis,
            CountryValuePair,
            GIICountryData,
            GIIData,
            GIIMetadata,
        )

        # Create a sample result that an integration test might return
        result = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="Human Development Report 2023-24",
                url=SAMPLE_PDF_URL,
                extraction_date="2024-01-15",
            ),
            gii_data=GIIData(
                metadata=GIIMetadata(data_year=2022, countries_total=170),
                countries=[
                    GIICountryData(name="Denmark", region="Europe", gii_value=0.013),
                    GIICountryData(name="Sweden", region="Europe", gii_value=0.023),
                ],
            ),
            european_analysis=EuropeanAnalysis(
                countries_count=2,
                average_gii=0.018,
                min_gii=CountryValuePair(country="Denmark", value=0.013),
                max_gii=CountryValuePair(country="Sweden", value=0.023),
                countries_included=["Denmark", "Sweden"],
            ),
        )

        # Validate it serializes correctly
        json_str = result.model_dump_json()
        assert "Denmark" in json_str
        assert "0.013" in json_str

        # Validate round-trip
        restored = HDIPDFAnalysisResult.model_validate_json(json_str)
        assert restored.european_analysis is not None
        assert restored.european_analysis.average_gii == 0.018
