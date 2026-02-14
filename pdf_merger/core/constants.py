"""
Constants for PDF Merger.
Composes domain-specific constant classes; import Constants from here for backward compatibility.
"""

from .file_constants import FileConstants
from .csv_serial_constants import CsvSerialConstants
from .license_constants import LicenseConstants
from .pdf_operations_constants import PdfOperationsConstants
from .excel_constants import ExcelConstants
from .ui_constants import UiConstants


class Constants(
    FileConstants,
    CsvSerialConstants,
    LicenseConstants,
    PdfOperationsConstants,
    ExcelConstants,
    UiConstants,
):
    """Configuration constants for PDF Merger (composed from domain modules)."""
    pass
