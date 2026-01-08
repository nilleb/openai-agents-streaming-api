"""Tests for HDI PDF Analyzer output models and structure validation."""

import pytest
from pydantic import ValidationError

from ..schemas.hdi_pdf_analyzer import (
    EUROPEAN_COUNTRIES,
    EUROPEAN_ISO_CODES,
    CountryValuePair,
    DocumentInfo,
    EuropeanAnalysis,
    ExtractionError,
    GIICountryData,
    GIIData,
    GIIMetadata,
    HDIPDFAnalysisResult,
    TOCEntry,
    compute_european_analysis,
    filter_european_countries,
    is_european_country,
)


class TestTOCEntry:
    """Tests for TOCEntry model."""

    def test_valid_toc_entry(self):
        """Test creating a valid TOC entry."""
        entry = TOCEntry(title="Introduction", page=1)
        assert entry.title == "Introduction"
        assert entry.page == 1
        assert entry.level == 1

    def test_toc_entry_with_level(self):
        """Test TOC entry with explicit level."""
        entry = TOCEntry(title="Section 1.1", page=5, level=2)
        assert entry.level == 2

    def test_toc_entry_invalid_page(self):
        """Test that page must be >= 1."""
        with pytest.raises(ValidationError) as exc_info:
            TOCEntry(title="Bad Entry", page=0)
        assert "page" in str(exc_info.value)

    def test_toc_entry_invalid_level(self):
        """Test that level must be between 1 and 5."""
        with pytest.raises(ValidationError):
            TOCEntry(title="Bad Level", page=1, level=6)


class TestDocumentInfo:
    """Tests for DocumentInfo model."""

    def test_valid_document_info(self):
        """Test creating valid document info."""
        info = DocumentInfo(
            title="Human Development Report 2023-24",
            url="https://hdr.undp.org/report.pdf",
            extraction_date="2024-01-15",
        )
        assert info.title == "Human Development Report 2023-24"
        assert info.pages is None

    def test_document_info_with_optional_fields(self):
        """Test document info with all optional fields."""
        info = DocumentInfo(
            title="HDR 2023-24",
            url="https://example.com/report.pdf",
            extraction_date="2024-01-15",
            author="UNDP",
            pages=400,
            data_year=2022,
        )
        assert info.author == "UNDP"
        assert info.pages == 400
        assert info.data_year == 2022

    def test_document_info_missing_required(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            DocumentInfo(title="Test")  # type: ignore


class TestGIICountryData:
    """Tests for GIICountryData model."""

    def test_valid_gii_country(self):
        """Test creating valid GII country data."""
        country = GIICountryData(
            name="Switzerland",
            region="Europe",
            gii_value=0.018,
        )
        assert country.name == "Switzerland"
        assert country.gii_value == 0.018
        assert country.gii_rank is None

    def test_gii_country_full_data(self):
        """Test GII country with all fields."""
        country = GIICountryData(
            name="Switzerland",
            iso_code="CHE",
            region="Europe",
            gii_value=0.018,
            gii_rank=1,
            maternal_mortality_ratio=7,
            adolescent_birth_rate=3.1,
            parliament_seats_female_pct=42.0,
            secondary_education_female_pct=97.0,
            secondary_education_male_pct=97.6,
            labour_participation_female_pct=62.0,
            labour_participation_male_pct=73.5,
        )
        assert country.iso_code == "CHE"
        assert country.gii_rank == 1
        assert country.maternal_mortality_ratio == 7

    def test_gii_value_bounds(self):
        """Test that GII value must be between 0 and 1."""
        with pytest.raises(ValidationError):
            GIICountryData(name="Bad", region="Test", gii_value=1.5)

        with pytest.raises(ValidationError):
            GIICountryData(name="Bad", region="Test", gii_value=-0.1)

    def test_iso_code_length(self):
        """Test that ISO code must be 3 characters."""
        with pytest.raises(ValidationError):
            GIICountryData(name="Test", iso_code="XX", region="Test", gii_value=0.5)

    def test_percentage_bounds(self):
        """Test that percentage fields are bounded 0-100."""
        with pytest.raises(ValidationError):
            GIICountryData(
                name="Test",
                region="Test",
                gii_value=0.5,
                parliament_seats_female_pct=150,
            )


class TestGIIData:
    """Tests for GIIData model."""

    def test_valid_gii_data(self):
        """Test creating valid GII data."""
        data = GIIData(
            metadata=GIIMetadata(data_year=2022, countries_total=170),
            countries=[
                GIICountryData(name="Switzerland", region="Europe", gii_value=0.018),
                GIICountryData(name="Denmark", region="Europe", gii_value=0.013),
            ],
        )
        assert len(data.countries) == 2
        assert data.metadata.data_year == 2022

    def test_empty_countries_list(self):
        """Test GII data with empty countries list."""
        data = GIIData(
            metadata=GIIMetadata(data_year=2022, countries_total=0),
            countries=[],
        )
        assert len(data.countries) == 0


class TestEuropeanAnalysis:
    """Tests for EuropeanAnalysis model."""

    def test_valid_european_analysis(self):
        """Test creating valid European analysis."""
        analysis = EuropeanAnalysis(
            countries_count=40,
            average_gii=0.089,
            min_gii=CountryValuePair(country="Denmark", value=0.013),
            max_gii=CountryValuePair(country="Albania", value=0.185),
            countries_included=["Denmark", "Sweden", "Norway"],
        )
        assert analysis.countries_count == 40
        assert analysis.average_gii == 0.089
        assert analysis.min_gii.country == "Denmark"

    def test_european_analysis_with_optional(self):
        """Test European analysis with optional fields."""
        analysis = EuropeanAnalysis(
            countries_count=40,
            average_gii=0.089,
            min_gii=CountryValuePair(country="Denmark", value=0.013),
            max_gii=CountryValuePair(country="Albania", value=0.185),
            median_gii=0.080,
            std_deviation=0.045,
            countries_included=["Denmark"],
        )
        assert analysis.median_gii == 0.080
        assert analysis.std_deviation == 0.045


class TestHDIPDFAnalysisResult:
    """Tests for complete HDIPDFAnalysisResult model."""

    def test_minimal_valid_result(self):
        """Test creating minimal valid result."""
        result = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="HDR 2023-24",
                url="https://example.com/report.pdf",
                extraction_date="2024-01-15",
            ),
        )
        assert result.document_info.title == "HDR 2023-24"
        assert result.gii_data is None
        assert result.european_analysis is None
        assert len(result.errors) == 0

    def test_full_result(self):
        """Test creating complete result with all fields."""
        result = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="Human Development Report 2023-24",
                url="https://hdr.undp.org/report.pdf",
                extraction_date="2024-01-15",
                author="UNDP",
                pages=400,
                data_year=2022,
            ),
            table_of_contents=[
                TOCEntry(title="Introduction", page=1),
                TOCEntry(title="Gender Inequality Index", page=250),
            ],
            gii_data=GIIData(
                metadata=GIIMetadata(data_year=2022, countries_total=170),
                countries=[
                    GIICountryData(
                        name="Switzerland", region="Europe", gii_value=0.018
                    ),
                ],
            ),
            european_analysis=EuropeanAnalysis(
                countries_count=40,
                average_gii=0.089,
                min_gii=CountryValuePair(country="Denmark", value=0.013),
                max_gii=CountryValuePair(country="Albania", value=0.185),
                countries_included=["Switzerland"],
            ),
            errors=[],
            processing_notes=["Extraction completed successfully"],
        )
        assert len(result.table_of_contents) == 2
        assert result.gii_data is not None
        assert result.european_analysis is not None

    def test_result_with_errors(self):
        """Test result with extraction errors."""
        result = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="HDR 2023-24",
                url="https://example.com/report.pdf",
                extraction_date="2024-01-15",
            ),
            errors=[
                ExtractionError(
                    step="gii_extraction",
                    error_type="ParseError",
                    message="Could not parse GII table",
                    recoverable=True,
                ),
            ],
        )
        assert len(result.errors) == 1
        assert result.errors[0].step == "gii_extraction"


class TestEuropeanCountryHelpers:
    """Tests for European country helper functions."""

    def test_is_european_country_by_name(self):
        """Test identifying European countries by name."""
        assert is_european_country("Germany") is True
        assert is_european_country("France") is True
        assert is_european_country("United Kingdom") is True
        assert is_european_country("Japan") is False
        assert is_european_country("Brazil") is False

    def test_is_european_country_case_insensitive(self):
        """Test case-insensitive country matching."""
        assert is_european_country("GERMANY") is True
        assert is_european_country("germany") is True
        assert is_european_country("Germany") is True

    def test_is_european_country_by_iso(self):
        """Test identifying European countries by ISO code."""
        assert is_european_country("Unknown", "DEU") is True
        assert is_european_country("Unknown", "FRA") is True
        assert is_european_country("Unknown", "JPN") is False

    def test_filter_european_countries(self):
        """Test filtering a list of countries to Europeans only."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.075),
            GIICountryData(name="Japan", region="Asia", gii_value=0.103),
            GIICountryData(name="France", region="Europe", gii_value=0.078),
            GIICountryData(name="Brazil", region="Americas", gii_value=0.408),
        ]
        european = filter_european_countries(countries)
        assert len(european) == 2
        assert all(c.name in ["Germany", "France"] for c in european)

    def test_european_countries_list_coverage(self):
        """Test that European countries list has expected countries."""
        assert "Germany" in EUROPEAN_COUNTRIES
        assert "France" in EUROPEAN_COUNTRIES
        assert "United Kingdom" in EUROPEAN_COUNTRIES
        assert "Poland" in EUROPEAN_COUNTRIES
        assert "Spain" in EUROPEAN_COUNTRIES
        assert "Italy" in EUROPEAN_COUNTRIES

    def test_european_iso_codes_coverage(self):
        """Test that ISO codes mapping is complete."""
        assert "DEU" in EUROPEAN_ISO_CODES
        assert "FRA" in EUROPEAN_ISO_CODES
        assert "GBR" in EUROPEAN_ISO_CODES
        assert EUROPEAN_ISO_CODES["DEU"] == "Germany"


class TestComputeEuropeanAnalysis:
    """Tests for compute_european_analysis function."""

    def test_compute_analysis_basic(self):
        """Test basic computation of European analysis."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.075),
            GIICountryData(name="France", region="Europe", gii_value=0.078),
            GIICountryData(name="Sweden", region="Europe", gii_value=0.039),
        ]
        analysis = compute_european_analysis(countries)

        assert analysis is not None
        assert analysis.countries_count == 3
        assert analysis.min_gii.country == "Sweden"
        assert analysis.min_gii.value == 0.039
        assert analysis.max_gii.country == "France"
        assert analysis.max_gii.value == 0.078

    def test_compute_analysis_average(self):
        """Test average computation."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.1),
            GIICountryData(name="France", region="Europe", gii_value=0.2),
        ]
        analysis = compute_european_analysis(countries)

        assert analysis is not None
        assert analysis.average_gii == 0.15

    def test_compute_analysis_filters_non_european(self):
        """Test that non-European countries are filtered out."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.075),
            GIICountryData(name="Japan", region="Asia", gii_value=0.103),
            GIICountryData(name="France", region="Europe", gii_value=0.078),
        ]
        analysis = compute_european_analysis(countries)

        assert analysis is not None
        assert analysis.countries_count == 2
        assert "Japan" not in analysis.countries_included

    def test_compute_analysis_empty_returns_none(self):
        """Test that empty input returns None."""
        analysis = compute_european_analysis([])
        assert analysis is None

    def test_compute_analysis_no_european_returns_none(self):
        """Test that no European countries returns None."""
        countries = [
            GIICountryData(name="Japan", region="Asia", gii_value=0.103),
            GIICountryData(name="Brazil", region="Americas", gii_value=0.408),
        ]
        analysis = compute_european_analysis(countries)
        assert analysis is None

    def test_compute_analysis_median_odd(self):
        """Test median computation with odd number of countries."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.1),
            GIICountryData(name="France", region="Europe", gii_value=0.2),
            GIICountryData(name="Sweden", region="Europe", gii_value=0.3),
        ]
        analysis = compute_european_analysis(countries)

        assert analysis is not None
        assert analysis.median_gii == 0.2

    def test_compute_analysis_median_even(self):
        """Test median computation with even number of countries."""
        countries = [
            GIICountryData(name="Germany", region="Europe", gii_value=0.1),
            GIICountryData(name="France", region="Europe", gii_value=0.2),
            GIICountryData(name="Sweden", region="Europe", gii_value=0.3),
            GIICountryData(name="Norway", region="Europe", gii_value=0.4),
        ]
        analysis = compute_european_analysis(countries)

        assert analysis is not None
        assert analysis.median_gii == 0.25


class TestJSONSerializationRoundTrip:
    """Tests for JSON serialization and deserialization."""

    def test_serialize_deserialize_result(self):
        """Test full round-trip serialization."""
        original = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="HDR 2023-24",
                url="https://example.com/report.pdf",
                extraction_date="2024-01-15",
            ),
            table_of_contents=[TOCEntry(title="Intro", page=1)],
            gii_data=GIIData(
                metadata=GIIMetadata(data_year=2022, countries_total=1),
                countries=[
                    GIICountryData(
                        name="Germany",
                        iso_code="DEU",
                        region="Europe",
                        gii_value=0.075,
                    )
                ],
            ),
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize back
        restored = HDIPDFAnalysisResult.model_validate_json(json_str)

        assert restored.document_info.title == original.document_info.title
        assert restored.gii_data is not None
        assert len(restored.gii_data.countries) == 1
        assert restored.gii_data.countries[0].name == "Germany"

    def test_serialize_to_dict(self):
        """Test serialization to dictionary."""
        result = HDIPDFAnalysisResult(
            document_info=DocumentInfo(
                title="HDR 2023-24",
                url="https://example.com/report.pdf",
                extraction_date="2024-01-15",
            ),
        )

        data = result.model_dump()

        assert isinstance(data, dict)
        assert data["document_info"]["title"] == "HDR 2023-24"
        assert data["gii_data"] is None
