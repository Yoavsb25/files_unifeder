"""
Enumerations for PDF Merger.
Centralized location for all type-safe enumerations.
"""

from enum import Enum


# ============================================================================
# Enumerations
# ============================================================================

class FileType(Enum):
    """File type enumeration."""
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"


class LicenseStatus(Enum):
    """License validation status."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID_SIGNATURE = "invalid_signature"
    NOT_FOUND = "not_found"
    INVALID_FORMAT = "invalid_format"
    VERSION_MISMATCH = "version_mismatch"


class MatchConfidence(Enum):
    """Confidence level of a match."""
    EXACT = "exact"
    STEM = "stem"
    LOW = "low"


class MatchBehavior(Enum):
    """Behavior when multiple matches are found."""
    FAIL_FAST = "fail_fast"
    WARN_FIRST = "warn_first"
    LOG_ALL = "log_all"


# RowStatus moved to pdf_merger.models.enums (domain layer). Re-export for backward compatibility.
from ..models import RowStatus  # noqa: F401

class LicenseColor(Enum):
    """License status colors for UI display."""
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"


class WarningLevel(Enum):
    """License expiry warning levels."""
    EXPIRED = "expired"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class StatusColor(Enum):
    """Status colors for UI components (footer, etc.)."""
    WHITE = "white"
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    BLUE = "blue"


class PageOrientation(Enum):
    """Page orientation for PDF generation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PageSize(Enum):
    """Page size for PDF generation."""
    LETTER = "letter"
    A4 = "A4"
