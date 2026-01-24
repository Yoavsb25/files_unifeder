"""
Constants and enumerations for PDF Merger.
Centralized location for all configuration constants.
"""

# File Extensions
EXCEL_FILE_EXTENSIONS = {'.xlsx', '.xls'}
CSV_FILE_EXTENSIONS = {'.csv'}
PDF_FILE_EXTENSIONS = {'.pdf'}
PDF_FILE_EXTENSION = '.pdf'  # Single extension string for string operations

# File Types
FILE_TYPE_EXCEL = 'excel'
FILE_TYPE_CSV = 'csv'
FILE_TYPE_PDF = 'pdf'

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
