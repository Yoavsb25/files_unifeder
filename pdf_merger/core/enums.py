"""
Enumerations for PDF Merger (core/operations/licensing).
MatchConfidence and MatchBehavior live in pdf_merger.models.enums; use those for matching.
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


# RowStatus is owned by the domain layer: use pdf_merger.models.RowStatus.
# LicenseColor and StatusColor moved to pdf_merger.ui.display_enums (UI-only).

class WarningLevel(Enum):
    """License expiry warning levels (used by licensing and UI)."""
    EXPIRED = "expired"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class PageOrientation(Enum):
    """Page orientation for PDF generation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PageSize(Enum):
    """Page size for PDF generation."""
    LETTER = "letter"
    A4 = "A4"
