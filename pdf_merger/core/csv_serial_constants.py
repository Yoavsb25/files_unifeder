"""CSV and serial number configuration constants for PDF Merger.
DEFAULT_SERIAL_NUMBERS_COLUMN must match pdf_merger.models.defaults.DEFAULT_SERIAL_NUMBERS_COLUMN (core cannot import models here to avoid circular import)."""


class CsvSerialConstants:
    """Column names, CSV parsing, and serial number format."""
    DEFAULT_SERIAL_NUMBERS_COLUMN = 'serial_numbers'
    GOLDFARB_SERIAL_NUMBER_COLUMN = 'Document ID'
    DEFAULT_CSV_DELIMITER = ','
    CSV_SAMPLE_SIZE = 1024
    UTF_8_ENCODING = 'utf-8'
    SERIAL_NUMBER_PREFIX = 'GRNW_'
    SERIAL_NUMBER_PREFIX_LOWER = 'grnw_'
    SERIAL_NUMBER_SEPARATOR = ','
