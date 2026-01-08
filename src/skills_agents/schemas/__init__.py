"""
Output schemas for skills agents.

This module contains Pydantic models for structured output from various skills.
"""

from .hdi_pdf_analyzer import (
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

__all__ = [
    "TOCEntry",
    "DocumentInfo",
    "GIICountryData",
    "GIIMetadata",
    "GIIData",
    "CountryValuePair",
    "EuropeanAnalysis",
    "ExtractionError",
    "HDIPDFAnalysisResult",
    "EUROPEAN_COUNTRIES",
    "EUROPEAN_ISO_CODES",
    "is_european_country",
    "filter_european_countries",
    "compute_european_analysis",
]
