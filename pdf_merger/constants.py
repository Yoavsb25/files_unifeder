"""
Constants for PDF Merger.
Centralized location for all configuration constants.
"""


# ============================================================================
# Constants Class
# ============================================================================

class Constants:
    """Configuration constants for PDF Merger."""
    
    # File Extensions
    EXCEL_FILE_EXTENSIONS = {'.xlsx', '.xls'}
    CSV_FILE_EXTENSIONS = {'.csv'}
    PDF_FILE_EXTENSIONS = {'.pdf'}
    PDF_FILE_EXTENSION = '.pdf'  # Single extension string for string operations
    
    # Source file extensions (files that can be merged - PDFs and Excel files)
    SOURCE_FILE_EXTENSIONS = PDF_FILE_EXTENSIONS | EXCEL_FILE_EXTENSIONS  # type: ignore
    
    # Default Column Names
    DEFAULT_SERIAL_NUMBERS_COLUMN = 'serial_numbers'
    
    # CSV Configuration
    DEFAULT_CSV_DELIMITER = ','
    CSV_SAMPLE_SIZE = 1024  # Bytes to read for delimiter detection
    UTF_8_ENCODING = 'utf-8'
    
    # Output File Configuration
    OUTPUT_FILENAME_PATTERN = 'merged_row_{}.pdf'
    
    # Serial Number Configuration
    SERIAL_NUMBER_PREFIX = 'GRNW_'
    SERIAL_NUMBER_PREFIX_LOWER = 'grnw_'
    SERIAL_NUMBER_SEPARATOR = ','  # Comma separator for multiple serial numbers
    
    # License Configuration
    LICENSE_DATE_FORMAT = '%Y-%m-%d'  # ISO format date string
    LICENSE_WARNING_CRITICAL_DAYS = 7  # Days until expiry for critical warning
    LICENSE_WARNING_WARNING_DAYS = 14  # Days until expiry for warning
    LICENSE_WARNING_INFO_DAYS = 30  # Days until expiry for info
    LICENSE_CLOCK_SKEW_TOLERANCE_MINUTES = 5  # Clock skew tolerance in minutes
    
    # PDF Operations Configuration
    STREAMING_THRESHOLD_MB = 100.0  # Memory threshold in MB for auto-enabling streaming
    STREAMING_CHUNK_SIZE = 10  # Number of pages to process per chunk in streaming mode
    STREAMING_PROGRESS_INTERVAL = 50  # Log progress every N pages for large files
    BYTES_PER_MB = 1024 * 1024  # Bytes per megabyte (for size calculations)
    MEMORY_MULTIPLIER_ESTIMATE = 2.5  # Estimated memory multiplier for PDF operations
    
    # Excel Converter Configuration
    DEFAULT_PAGE_SIZE = 'letter'  # Default page size for Excel to PDF conversion
    DEFAULT_ORIENTATION = 'portrait'  # Default orientation for Excel to PDF conversion
    DEFAULT_MAX_COLS_PER_PAGE = 8  # Default maximum columns per page for wide tables
    
    # UI/Display Configuration
    MAX_DISPLAY_STRING_LENGTH = 100  # Maximum length for displaying strings before truncation
    PERCENTAGE_MULTIPLIER = 100.0  # Multiplier for percentage calculations (0.0 to 100.0)
