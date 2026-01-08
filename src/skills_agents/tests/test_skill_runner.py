"""
Skill Runner Test Framework

Provides a repeatable structure for running skill-based tests and gathering results.
This framework enables:
- Loading and validating skills
- Running skills against sample inputs
- Collecting structured results
- Generating test reports
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


from ..builder import SkillBuilder
from ..discovery import discover_skills
from ..loader import load_top_level_agents
from ..models import SkillConfig
from ..validator import SkillValidator


logger = logging.getLogger(__name__)

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@dataclass
class SkillTestResult:
    """Result from running a skill test."""

    skill_name: str
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    output_data: Optional[dict[str, Any]] = None
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class SkillTestReport:
    """Aggregated test report for skill testing."""

    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skills_tested: list[str]
    results: list[SkillTestResult]

    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": f"{self.success_rate:.1f}%",
            "skills_tested": self.skills_tested,
            "results": [
                {
                    "skill": r.skill_name,
                    "test": r.test_name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message,
                }
                for r in self.results
            ],
        }

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class SkillTestRunner:
    """Runner for executing skill tests and collecting results."""

    def __init__(
        self,
        skills_directory: Optional[Path] = None,
        strict_validation: bool = False,
    ):
        self.skills_directory = skills_directory or EXAMPLES_DIR
        self.strict_validation = strict_validation
        self.validator = SkillValidator(strict=strict_validation)
        self.builder = SkillBuilder()
        self.results: list[SkillTestResult] = []
        self._discovered_skills: dict[str, SkillConfig] = {}

    def discover_all_skills(self) -> dict[str, SkillConfig]:
        """Discover all skills in the skills directory."""
        if not self._discovered_skills:
            for skill_config in discover_skills(self.skills_directory):
                self._discovered_skills[skill_config.name] = skill_config
        return self._discovered_skills

    def validate_skill(self, skill_name: str) -> SkillTestResult:
        """Validate a single skill and return result."""
        start_time = datetime.now()

        skills = self.discover_all_skills()
        if skill_name not in skills:
            return SkillTestResult(
                skill_name=skill_name,
                test_name="validation",
                passed=False,
                duration_ms=0,
                error_message=f"Skill '{skill_name}' not found",
            )

        config = skills[skill_name]
        result = self.validator.validate_skill_config(config)

        duration = (datetime.now() - start_time).total_seconds() * 1000

        return SkillTestResult(
            skill_name=skill_name,
            test_name="validation",
            passed=result.is_valid,
            duration_ms=duration,
            error_message=None
            if result.is_valid
            else "; ".join(e.message for e in result.errors),
            validation_errors=[e.message for e in result.errors],
        )

    def validate_all_skills(self) -> list[SkillTestResult]:
        """Validate all discovered skills."""
        results = []
        for skill_name in self.discover_all_skills():
            result = self.validate_skill(skill_name)
            results.append(result)
            self.results.append(result)
        return results

    def build_agent(self, skill_name: str) -> SkillTestResult:
        """Test building an agent from a skill."""
        start_time = datetime.now()

        skills = self.discover_all_skills()
        if skill_name not in skills:
            return SkillTestResult(
                skill_name=skill_name,
                test_name="agent_build",
                passed=False,
                duration_ms=0,
                error_message=f"Skill '{skill_name}' not found",
            )

        config = skills[skill_name]
        error_message = None
        passed = True

        try:
            agent = self.builder.build_agent_from_skill(config)
            instructions = agent.instructions
            instructions_len = len(instructions) if isinstance(instructions, str) else 0
            output_data = {
                "agent_name": agent.name,
                "model": agent.model,
                "instructions_length": instructions_len,
                "tools_count": len(agent.tools) if agent.tools else 0,
            }
        except Exception as e:
            passed = False
            error_message = str(e)
            output_data = None

        duration = (datetime.now() - start_time).total_seconds() * 1000

        return SkillTestResult(
            skill_name=skill_name,
            test_name="agent_build",
            passed=passed,
            duration_ms=duration,
            error_message=error_message,
            output_data=output_data,
        )

    def generate_report(self) -> SkillTestReport:
        """Generate a test report from collected results."""
        skills_tested = list(set(r.skill_name for r in self.results))
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        return SkillTestReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.results),
            passed_tests=passed,
            failed_tests=failed,
            skills_tested=skills_tested,
            results=self.results,
        )

    def reset(self) -> None:
        """Reset collected results."""
        self.results = []
        self.builder.clear_cache()


class TestSkillDiscovery:
    """Tests for skill discovery functionality."""

    def test_discover_examples(self):
        """Test that example skills are discovered."""
        runner = SkillTestRunner()
        skills = runner.discover_all_skills()

        # Should find the example skills
        assert len(skills) >= 4
        assert "code-review" in skills
        assert "data-analysis" in skills
        assert "research-assistant" in skills
        assert "task-orchestrator" in skills

    def test_discover_hdi_skills(self):
        """Test that HDI analyzer skills are discovered."""
        runner = SkillTestRunner()
        skills = runner.discover_all_skills()

        # Should find the new HDI-related skills
        assert "hdi-pdf-analyzer" in skills
        assert "pdf-extractor" in skills
        assert "gii-extractor" in skills
        assert "data-aggregator" in skills


class TestSkillValidation:
    """Tests for skill validation functionality."""

    def test_validate_all_skills(self):
        """Test that all discovered skills pass validation."""
        runner = SkillTestRunner()
        results = runner.validate_all_skills()

        for result in results:
            assert result.passed, (
                f"Skill '{result.skill_name}' failed validation: {result.error_message}"
            )

    def test_validate_hdi_analyzer(self):
        """Test HDI analyzer skill validation."""
        runner = SkillTestRunner()
        result = runner.validate_skill("hdi-pdf-analyzer")

        assert result.passed
        assert result.skill_name == "hdi-pdf-analyzer"

    def test_validate_sub_agents(self):
        """Test validation of HDI analyzer sub-agent skills."""
        runner = SkillTestRunner()
        sub_agents = ["pdf-extractor", "gii-extractor", "data-aggregator"]

        for agent in sub_agents:
            result = runner.validate_skill(agent)
            assert result.passed, f"Sub-agent '{agent}' failed: {result.error_message}"


class TestAgentBuilding:
    """Tests for agent building functionality."""

    def test_build_all_agents(self):
        """Test building agents from all skills."""
        runner = SkillTestRunner()
        skills = runner.discover_all_skills()

        for skill_name in skills:
            result = runner.build_agent(skill_name)
            assert result.passed, (
                f"Failed to build agent for '{skill_name}': {result.error_message}"
            )
            assert result.output_data is not None
            assert result.output_data["instructions_length"] > 0

    def test_build_hdi_analyzer(self):
        """Test building the HDI analyzer agent."""
        runner = SkillTestRunner()
        result = runner.build_agent("hdi-pdf-analyzer")

        assert result.passed
        assert result.output_data is not None
        assert (
            "HDI" in result.output_data["agent_name"]
            or "Hdi" in result.output_data["agent_name"]
        )


class TestReportGeneration:
    """Tests for test report generation."""

    def test_generate_report(self):
        """Test generating a test report."""
        runner = SkillTestRunner()
        runner.validate_all_skills()
        report = runner.generate_report()

        assert report.total_tests > 0
        assert report.passed_tests >= 0
        assert report.failed_tests >= 0
        assert report.total_tests == report.passed_tests + report.failed_tests
        assert len(report.skills_tested) > 0

    def test_report_to_json(self):
        """Test converting report to JSON."""
        runner = SkillTestRunner()
        runner.validate_all_skills()
        report = runner.generate_report()

        json_str = report.to_json()
        data = json.loads(json_str)

        assert "timestamp" in data
        assert "total_tests" in data
        assert "success_rate" in data
        assert "results" in data

    def test_report_success_rate(self):
        """Test report success rate calculation."""
        runner = SkillTestRunner()
        runner.validate_all_skills()
        report = runner.generate_report()

        # All example skills should pass validation
        assert report.success_rate >= 90.0


class TestTopLevelAgents:
    """Tests for top-level agents configuration."""

    def test_load_top_level_agents(self):
        """Test loading top-level agents from config."""
        config_path = EXAMPLES_DIR / "agents.yaml"
        agents = load_top_level_agents(config_path)

        assert len(agents) > 0
        assert "Orchestrator" in agents
        assert "HDI PDF Analyzer" in agents

    def test_hdi_analyzer_has_sub_agents(self):
        """Test that HDI analyzer has sub-agents configured."""
        config_path = EXAMPLES_DIR / "agents.yaml"
        agents = load_top_level_agents(config_path)

        hdi_analyzer = agents.get("HDI PDF Analyzer")
        assert hdi_analyzer is not None
        assert hdi_analyzer.tools is not None
        assert (
            len(hdi_analyzer.tools) == 3
        )  # pdf-extractor, gii-extractor, data-aggregator


class TestSkillOutputModels:
    """Tests for skill output model integration."""

    def test_hdi_output_models_importable(self):
        """Test that HDI output models can be imported."""
        from ..schemas.hdi_pdf_analyzer import (
            HDIPDFAnalysisResult,
            GIICountryData,
            EuropeanAnalysis,
        )

        assert HDIPDFAnalysisResult is not None
        assert GIICountryData is not None
        assert EuropeanAnalysis is not None

    def test_output_models_have_schema(self):
        """Test that output models have JSON schema."""
        from ..schemas.hdi_pdf_analyzer import HDIPDFAnalysisResult

        schema = HDIPDFAnalysisResult.model_json_schema()
        assert "properties" in schema
        assert "document_info" in schema["properties"]
        assert "gii_data" in schema["properties"]
        assert "european_analysis" in schema["properties"]
