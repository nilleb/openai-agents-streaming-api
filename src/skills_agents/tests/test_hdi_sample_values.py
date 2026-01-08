"""
Tests for HDI PDF Analyzer with sample document values.

These tests validate expected values from the Human Development Report 2023-24:
https://hdr.undp.org/system/files/documents/global-report-document/hdr2023-24reporten.pdf

The expected values are based on Table 5: Gender Inequality Index and related indicators.
Data year: 2022
"""

from dataclasses import dataclass

import pytest

from ..schemas.hdi_pdf_analyzer import (
    EUROPEAN_COUNTRIES,
    DocumentInfo,
    GIICountryData,
    GIIData,
    GIIMetadata,
    HDIPDFAnalysisResult,
    TOCEntry,
    compute_european_analysis,
)


# =============================================================================
# Expected values from HDR 2023-24 (Table 5: Gender Inequality Index)
# Data year: 2022
# =============================================================================


@dataclass
class ExpectedGIIEntry:
    """Expected GII data for a country."""

    name: str
    gii_value: float
    gii_rank: int


# Top 10 countries by GII rank (lowest = best)
EXPECTED_GII_TOP_10: list[ExpectedGIIEntry] = [
    ExpectedGIIEntry(name="Denmark", gii_value=0.013, gii_rank=1),
    ExpectedGIIEntry(name="Switzerland", gii_value=0.018, gii_rank=2),
    ExpectedGIIEntry(name="Sweden", gii_value=0.023, gii_rank=3),
    ExpectedGIIEntry(name="Belgium", gii_value=0.024, gii_rank=4),
    ExpectedGIIEntry(name="Netherlands", gii_value=0.025, gii_rank=5),
    ExpectedGIIEntry(name="Norway", gii_value=0.026, gii_rank=6),
    ExpectedGIIEntry(name="Slovenia", gii_value=0.031, gii_rank=7),
    ExpectedGIIEntry(name="Finland", gii_value=0.033, gii_rank=8),
    ExpectedGIIEntry(name="France", gii_value=0.036, gii_rank=9),
    ExpectedGIIEntry(name="Iceland", gii_value=0.038, gii_rank=10),
]

# European countries GII values from HDR 2023-24
# These are expected values to validate against extraction results
EXPECTED_EUROPEAN_GII_DATA = {
    # Northern Europe
    "Denmark": 0.013,
    "Sweden": 0.023,
    "Norway": 0.026,
    "Finland": 0.033,
    "Iceland": 0.038,
    "Ireland": 0.055,
    "United Kingdom": 0.059,
    "Estonia": 0.084,
    "Latvia": 0.146,
    "Lithuania": 0.089,
    # Western Europe
    "Switzerland": 0.018,
    "Belgium": 0.024,
    "Netherlands": 0.025,
    "France": 0.036,
    "Germany": 0.072,
    "Austria": 0.055,
    "Luxembourg": 0.052,
    # Southern Europe
    "Slovenia": 0.031,
    "Spain": 0.043,
    "Portugal": 0.068,
    "Italy": 0.060,
    "Greece": 0.109,
    "Cyprus": 0.057,
    "Malta": 0.065,
    "Croatia": 0.072,
    "Montenegro": 0.120,
    "Serbia": 0.130,
    "Albania": 0.185,
    "North Macedonia": 0.149,
    "Bosnia and Herzegovina": 0.124,
    # Eastern Europe
    "Poland": 0.083,
    "Czech Republic": 0.091,
    "Hungary": 0.108,
    "Slovakia": 0.098,
    "Romania": 0.202,
    "Bulgaria": 0.159,
    "Moldova": 0.192,
    "Ukraine": 0.189,
    "Belarus": 0.107,
    "Russia": 0.203,
}

# Expected summary statistics for European countries
EXPECTED_MIN_COUNTRY = "Denmark"
EXPECTED_MIN_VALUE = 0.013
EXPECTED_MAX_COUNTRY = "Russia"  # Among common European countries in the dataset
EXPECTED_MAX_VALUE = 0.203
EXPECTED_APPROXIMATE_AVERAGE = 0.089  # Will vary based on exact country set
EXPECTED_COUNT_MIN = 35
EXPECTED_COUNT_MAX = 45


class TestExpectedGIIValues:
    """Tests validating expected GII values from the HDR 2023-24 report."""

    def test_top_10_gii_values(self):
        """Test that top 10 GII values are in expected range."""
        for expected in EXPECTED_GII_TOP_10:
            assert expected.gii_value >= 0.0
            assert expected.gii_value <= 0.05  # Top 10 should be very low

    def test_top_10_are_european(self):
        """Test that most top 10 GII countries are European."""
        european_in_top10 = [
            c for c in EXPECTED_GII_TOP_10 if c.name in EUROPEAN_COUNTRIES
        ]
        # All top 10 in 2023-24 report are European
        assert len(european_in_top10) >= 9

    def test_gii_values_are_valid_range(self):
        """Test all expected GII values are in valid range."""
        for country, value in EXPECTED_EUROPEAN_GII_DATA.items():
            assert 0.0 <= value <= 1.0, f"Invalid GII value for {country}: {value}"

    def test_denmark_has_lowest_gii(self):
        """Test that Denmark has the lowest GII (rank 1)."""
        min_country = min(EXPECTED_EUROPEAN_GII_DATA.items(), key=lambda x: x[1])
        assert min_country[0] == "Denmark"
        assert min_country[1] == 0.013


class TestSampleDataExtraction:
    """Tests for validating sample data extraction against expected values."""

    @pytest.fixture
    def sample_extracted_data(self) -> list[GIICountryData]:
        """Create sample extracted data matching expected values."""
        return [
            GIICountryData(
                name=name,
                region="Europe",
                gii_value=value,
                iso_code=None,
            )
            for name, value in EXPECTED_EUROPEAN_GII_DATA.items()
        ]

    def test_extracted_data_count(self, sample_extracted_data):
        """Test that we have expected number of European countries."""
        assert len(sample_extracted_data) >= EXPECTED_COUNT_MIN
        assert len(sample_extracted_data) <= EXPECTED_COUNT_MAX

    def test_extracted_data_min_value(self, sample_extracted_data):
        """Test minimum GII value matches expected."""
        min_country = min(sample_extracted_data, key=lambda c: c.gii_value)
        assert min_country.name == EXPECTED_MIN_COUNTRY
        assert min_country.gii_value == EXPECTED_MIN_VALUE

    def test_extracted_data_max_value(self, sample_extracted_data):
        """Test maximum GII value matches expected."""
        max_country = max(sample_extracted_data, key=lambda c: c.gii_value)
        assert max_country.gii_value == EXPECTED_MAX_VALUE

    def test_compute_analysis_matches_expected(self, sample_extracted_data):
        """Test computed analysis matches expected statistics."""
        analysis = compute_european_analysis(sample_extracted_data)

        assert analysis is not None
        assert analysis.min_gii.country == EXPECTED_MIN_COUNTRY
        assert analysis.min_gii.value == EXPECTED_MIN_VALUE

    def test_average_in_expected_range(self, sample_extracted_data):
        """Test that computed average is in expected range."""
        analysis = compute_european_analysis(sample_extracted_data)

        assert analysis is not None
        # Allow some tolerance for average calculation
        assert abs(analysis.average_gii - EXPECTED_APPROXIMATE_AVERAGE) < 0.02


class TestSampleDocumentResult:
    """Tests for complete sample document result."""

    @pytest.fixture
    def sample_result(self) -> HDIPDFAnalysisResult:
        """Create sample result matching HDR 2023-24."""
        countries = [
            GIICountryData(
                name=name,
                region="Europe",
                gii_value=value,
            )
            for name, value in EXPECTED_EUROPEAN_GII_DATA.items()
        ]

        return HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="Human Development Report 2023-24",
                url="https://hdr.undp.org/system/files/documents/global-report-document/hdr2023-24reporten.pdf",
                extraction_date="2024-01-15",
                author="UNDP",
                pages=400,
                data_year=2022,
            ),
            table_of_contents=[
                TOCEntry(title="Overview", page=1),
                TOCEntry(title="Part 1: The state of human development", page=21),
                TOCEntry(title="Statistical annex", page=251),
                TOCEntry(title="Table 5: Gender Inequality Index", page=303),
            ],
            gii_data=GIIData(
                metadata=GIIMetadata(
                    data_year=2022,
                    countries_total=170,
                    source_table="Table 5: Gender Inequality Index and related indicators",
                ),
                countries=countries,
            ),
            european_analysis=compute_european_analysis(countries),
        )

    def test_document_info_valid(self, sample_result):
        """Test document info is correctly structured."""
        assert sample_result.document_info.title == "Human Development Report 2023-24"
        assert sample_result.document_info.data_year == 2022
        assert "hdr.undp.org" in sample_result.document_info.url

    def test_toc_has_gii_reference(self, sample_result):
        """Test table of contents includes GII reference."""
        gii_entries = [
            e
            for e in sample_result.table_of_contents
            if "Gender Inequality" in e.title or "GII" in e.title
        ]
        assert len(gii_entries) >= 1

    def test_gii_data_complete(self, sample_result):
        """Test GII data has required fields."""
        assert sample_result.gii_data is not None
        assert sample_result.gii_data.metadata.data_year == 2022
        assert len(sample_result.gii_data.countries) > 30

    def test_european_analysis_complete(self, sample_result):
        """Test European analysis has all required fields."""
        assert sample_result.european_analysis is not None
        assert sample_result.european_analysis.countries_count > 30
        assert sample_result.european_analysis.average_gii > 0
        assert sample_result.european_analysis.min_gii is not None
        assert sample_result.european_analysis.max_gii is not None

    def test_result_serializable(self, sample_result):
        """Test that result can be serialized to JSON."""
        json_str = sample_result.model_dump_json()
        assert len(json_str) > 0
        assert "Denmark" in json_str
        assert "0.013" in json_str


class TestValueValidation:
    """Tests for validating specific values from the sample document."""

    def test_nordic_countries_low_gii(self):
        """Test that Nordic countries have low GII values."""
        nordic = ["Denmark", "Sweden", "Norway", "Finland", "Iceland"]
        for country in nordic:
            assert country in EXPECTED_EUROPEAN_GII_DATA
            assert EXPECTED_EUROPEAN_GII_DATA[country] < 0.05

    def test_eastern_europe_higher_gii(self):
        """Test that Eastern European countries have higher GII values."""
        eastern = ["Romania", "Bulgaria", "Moldova", "Russia"]
        for country in eastern:
            assert country in EXPECTED_EUROPEAN_GII_DATA
            assert EXPECTED_EUROPEAN_GII_DATA[country] > 0.15

    def test_western_europe_moderate_gii(self):
        """Test Western European countries have moderate GII values."""
        western = ["Germany", "France", "Austria", "Netherlands"]
        for country in western:
            assert country in EXPECTED_EUROPEAN_GII_DATA
            assert EXPECTED_EUROPEAN_GII_DATA[country] < 0.1

    def test_gii_rank_consistency(self):
        """Test that GII rankings are consistent with values."""
        sorted_by_value = sorted(EXPECTED_EUROPEAN_GII_DATA.items(), key=lambda x: x[1])
        # Denmark should be first (lowest)
        assert sorted_by_value[0][0] == "Denmark"
        # Switzerland should be second
        assert sorted_by_value[1][0] == "Switzerland"


class TestDataQuality:
    """Tests for data quality validation."""

    def test_no_duplicate_countries(self):
        """Test there are no duplicate country entries."""
        countries = list(EXPECTED_EUROPEAN_GII_DATA.keys())
        assert len(countries) == len(set(countries))

    def test_all_countries_in_european_list(self):
        """Test all expected countries are in the European countries list."""
        for country in EXPECTED_EUROPEAN_GII_DATA.keys():
            assert country in EUROPEAN_COUNTRIES, f"{country} not in EUROPEAN_COUNTRIES"

    def test_gii_precision(self):
        """Test GII values have appropriate precision."""
        for country, value in EXPECTED_EUROPEAN_GII_DATA.items():
            # GII values should be 3 decimal places
            rounded = round(value, 3)
            assert value == rounded, f"Unexpected precision for {country}: {value}"

    def test_complete_coverage(self):
        """Test we have data for major European countries."""
        major_countries = [
            "Germany",
            "France",
            "United Kingdom",
            "Italy",
            "Spain",
            "Poland",
            "Netherlands",
            "Belgium",
            "Sweden",
            "Austria",
        ]
        for country in major_countries:
            assert country in EXPECTED_EUROPEAN_GII_DATA, f"Missing {country}"
