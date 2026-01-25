"""
PDF Merger Package
A modular package for merging PDFs based on serial numbers from CSV/Excel files.
"""

__version__ = '1.0.0'
APP_VERSION = '1.0.0'  # Application version for licensing and display
APP_NAME = 'PDF Batch Merger'  # Application name for UI display

# Import main functions for easy access
from .processor import process_file, ProcessingResult
from .pdf_operations import find_pdf_file, find_source_file, merge_pdfs
from .data_parser import split_serial_numbers
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
    # Version and App Info
    'APP_VERSION',
    'APP_NAME',
    # Main processing
    'process_file',
    'ProcessingResult',
    # PDF operations (useful for external use)
    'find_pdf_file',
    'find_source_file',
    'merge_pdfs',
    # Data parsing (useful for external use)
    'split_serial_numbers',
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
