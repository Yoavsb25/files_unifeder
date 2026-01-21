"""
PDF Merger Package
A modular package for merging PDFs based on serial numbers from CSV/Excel files.
"""

__version__ = '1.0.0'
APP_VERSION = '1.0.0'  # Application version for licensing and display

# Import main functions for easy access
from .processor import process_file, ProcessingResult
from .pdf_operations import find_pdf_file, merge_pdfs
from .data_parser import parse_serial_numbers
from .file_reader import read_data_file, get_file_columns
from .validators import validate_file, validate_folder, validate_paths, validate_serial_number
from .exceptions import (
    PDFMergerError,
    FileNotFoundError,
    InvalidFileFormatError,
    MissingColumnError,
    PDFProcessingError,
    ValidationError,
)

# Public API - functions intended for external use
__all__ = [
    # Version
    'APP_VERSION',
    # Main processing
    'process_file',
    'ProcessingResult',
    # PDF operations (useful for external use)
    'find_pdf_file',
    'merge_pdfs',
    # Data parsing (useful for external use)
    'parse_serial_numbers',
    # File reading (useful for external use)
    'read_data_file',
    'get_file_columns',
    # Validation (useful for external use)
    'validate_file',
    'validate_folder',
    'validate_paths',
    'validate_serial_number',
    # Exceptions
    'PDFMergerError',
    'FileNotFoundError',
    'InvalidFileFormatError',
    'MissingColumnError',
    'PDFProcessingError',
    'ValidationError',
]
