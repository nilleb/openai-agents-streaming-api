"""
Pydantic models for HDI PDF Analyzer structured output.

These models define the expected output schema from the HDI PDF analysis workflow.
They can be used for validation, testing, and as OpenAI structured output types.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TOCEntry(BaseModel):
    """A single entry in the table of contents."""

    title: str = Field(..., description="Section or chapter title")
    page: int = Field(..., ge=1, description="Page number where section starts")
    level: int = Field(default=1, ge=1, le=5, description="Heading level (1=top)")


class DocumentInfo(BaseModel):
    """Information about the source PDF document."""

    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Source URL of the document")
    extraction_date: str = Field(
        ..., description="Date of data extraction (ISO format)"
    )
    author: Optional[str] = Field(
        default=None, description="Document author/organization"
    )
    pages: Optional[int] = Field(
        default=None, ge=1, description="Total pages in document"
    )
    data_year: Optional[int] = Field(
        default=None, description="Year the data refers to"
    )


class GIICountryData(BaseModel):
    """Gender Inequality Index data for a single country."""

    name: str = Field(..., description="Country name (standardized)")
    iso_code: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 3166-1 alpha-3 country code",
    )
    region: str = Field(..., description="Geographic region classification")
    gii_value: float = Field(
        ..., ge=0.0, le=1.0, description="GII value (0=equality, 1=inequality)"
    )
    gii_rank: Optional[int] = Field(
        default=None, ge=1, description="GII rank among all countries"
    )

    # Component indicators (optional, may not be in all extractions)
    maternal_mortality_ratio: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maternal mortality ratio per 100,000 live births",
    )
    adolescent_birth_rate: Optional[float] = Field(
        default=None,
        ge=0,
        description="Adolescent birth rate per 1,000 women ages 15-19",
    )
    parliament_seats_female_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Share of seats in parliament held by women (%)",
    )
    secondary_education_female_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Population with at least secondary education, female (%)",
    )
    secondary_education_male_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Population with at least secondary education, male (%)",
    )
    labour_participation_female_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Labour force participation rate, female (%)",
    )
    labour_participation_male_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Labour force participation rate, male (%)",
    )


class GIIMetadata(BaseModel):
    """Metadata about the GII data extraction."""

    description: str = Field(
        default="Gender Inequality Index measures gender-based disadvantage",
        description="Description of what GII measures",
    )
    data_year: int = Field(..., description="Year the GII data refers to")
    countries_total: int = Field(
        ..., ge=0, description="Total number of countries with GII data"
    )
    source_table: Optional[str] = Field(
        default=None, description="Name/number of source table in document"
    )


class GIIData(BaseModel):
    """Complete GII dataset from the document."""

    metadata: GIIMetadata = Field(..., description="Metadata about the GII extraction")
    countries: list[GIICountryData] = Field(
        default_factory=list, description="GII data for all countries"
    )


class CountryValuePair(BaseModel):
    """A country with its associated value."""

    country: str = Field(..., description="Country name")
    value: float = Field(..., description="Associated value (e.g., GII)")


class EuropeanAnalysis(BaseModel):
    """Analysis results for European countries."""

    countries_count: int = Field(
        ..., ge=0, description="Number of European countries analyzed"
    )
    average_gii: float = Field(
        ..., ge=0.0, le=1.0, description="Average GII for European countries"
    )
    min_gii: CountryValuePair = Field(..., description="Country with lowest (best) GII")
    max_gii: CountryValuePair = Field(
        ..., description="Country with highest (worst) GII"
    )
    median_gii: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Median GII value"
    )
    std_deviation: Optional[float] = Field(
        default=None, ge=0, description="Standard deviation of GII values"
    )
    countries_included: list[str] = Field(
        default_factory=list, description="List of countries included in analysis"
    )


class ExtractionError(BaseModel):
    """Details about an extraction error."""

    step: str = Field(..., description="Processing step where error occurred")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    recoverable: bool = Field(
        default=True, description="Whether processing could continue"
    )


class HDIPDFAnalysisResult(BaseModel):
    """
    Complete structured output from HDI PDF analysis.

    This is the main output model for the hdi-pdf-analyzer agent.
    """

    document_info: DocumentInfo = Field(
        ..., description="Information about the source document"
    )
    table_of_contents: list[TOCEntry] = Field(
        default_factory=list, description="Extracted table of contents"
    )
    gii_data: Optional[GIIData] = Field(
        default=None, description="Extracted GII data for all countries"
    )
    european_analysis: Optional[EuropeanAnalysis] = Field(
        default=None, description="Analysis results for European countries"
    )
    errors: list[ExtractionError] = Field(
        default_factory=list, description="Any errors during extraction"
    )
    processing_notes: list[str] = Field(
        default_factory=list, description="Notes about the extraction process"
    )


# European countries list for filtering
EUROPEAN_COUNTRIES = [
    # Western Europe
    "Austria",
    "Belgium",
    "France",
    "Germany",
    "Liechtenstein",
    "Luxembourg",
    "Monaco",
    "Netherlands",
    "Switzerland",
    # Northern Europe
    "Denmark",
    "Estonia",
    "Finland",
    "Iceland",
    "Ireland",
    "Latvia",
    "Lithuania",
    "Norway",
    "Sweden",
    "United Kingdom",
    # Southern Europe
    "Albania",
    "Andorra",
    "Bosnia and Herzegovina",
    "Croatia",
    "Cyprus",
    "Greece",
    "Italy",
    "Malta",
    "Montenegro",
    "North Macedonia",
    "Portugal",
    "San Marino",
    "Serbia",
    "Slovenia",
    "Spain",
    # Eastern Europe
    "Belarus",
    "Bulgaria",
    "Czech Republic",
    "Czechia",  # Alternative name
    "Hungary",
    "Moldova",
    "Poland",
    "Romania",
    "Russia",
    "Russian Federation",  # Alternative name
    "Slovakia",
    "Ukraine",
    "Kosovo",
]

# ISO codes mapping for European countries
EUROPEAN_ISO_CODES = {
    "ALB": "Albania",
    "AND": "Andorra",
    "AUT": "Austria",
    "BLR": "Belarus",
    "BEL": "Belgium",
    "BIH": "Bosnia and Herzegovina",
    "BGR": "Bulgaria",
    "HRV": "Croatia",
    "CYP": "Cyprus",
    "CZE": "Czech Republic",
    "DNK": "Denmark",
    "EST": "Estonia",
    "FIN": "Finland",
    "FRA": "France",
    "DEU": "Germany",
    "GRC": "Greece",
    "HUN": "Hungary",
    "ISL": "Iceland",
    "IRL": "Ireland",
    "ITA": "Italy",
    "XKX": "Kosovo",
    "LVA": "Latvia",
    "LIE": "Liechtenstein",
    "LTU": "Lithuania",
    "LUX": "Luxembourg",
    "MLT": "Malta",
    "MDA": "Moldova",
    "MCO": "Monaco",
    "MNE": "Montenegro",
    "NLD": "Netherlands",
    "MKD": "North Macedonia",
    "NOR": "Norway",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "RUS": "Russia",
    "SMR": "San Marino",
    "SRB": "Serbia",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "ESP": "Spain",
    "SWE": "Sweden",
    "CHE": "Switzerland",
    "UKR": "Ukraine",
    "GBR": "United Kingdom",
}


def is_european_country(country_name: str, iso_code: Optional[str] = None) -> bool:
    """Check if a country is European by name or ISO code."""
    # Check by name
    normalized_name = country_name.strip()
    if normalized_name in EUROPEAN_COUNTRIES:
        return True

    # Check case-insensitive
    for european in EUROPEAN_COUNTRIES:
        if european.lower() == normalized_name.lower():
            return True

    # Check by ISO code
    if iso_code and iso_code.upper() in EUROPEAN_ISO_CODES:
        return True

    return False


def filter_european_countries(countries: list[GIICountryData]) -> list[GIICountryData]:
    """Filter a list of GII country data to only European countries."""
    return [c for c in countries if is_european_country(c.name, c.iso_code)]


def compute_european_analysis(
    countries: list[GIICountryData],
) -> Optional[EuropeanAnalysis]:
    """Compute analysis statistics for European countries."""
    european = filter_european_countries(countries)

    if not european:
        return None

    gii_values = [c.gii_value for c in european]
    avg_gii = sum(gii_values) / len(gii_values)

    # Find min and max
    min_country = min(european, key=lambda c: c.gii_value)
    max_country = max(european, key=lambda c: c.gii_value)

    # Compute median
    sorted_values = sorted(gii_values)
    n = len(sorted_values)
    if n % 2 == 0:
        median = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    else:
        median = sorted_values[n // 2]

    # Compute standard deviation
    variance = sum((x - avg_gii) ** 2 for x in gii_values) / len(gii_values)
    std_dev = variance**0.5

    return EuropeanAnalysis(
        countries_count=len(european),
        average_gii=round(avg_gii, 4),
        min_gii=CountryValuePair(country=min_country.name, value=min_country.gii_value),
        max_gii=CountryValuePair(country=max_country.name, value=max_country.gii_value),
        median_gii=round(median, 4),
        std_deviation=round(std_dev, 4),
        countries_included=[c.name for c in european],
    )
