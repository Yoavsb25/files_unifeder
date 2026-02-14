"""
Read column names from CSV/Excel data files.
Lives in utils so validators do not depend on core.csv_excel_reader.
"""

from pathlib import Path
from typing import List
import csv

from .exceptions import InvalidFileFormatError

# Extensions for data files (single source for column_reader; must match core.file_constants for consistency)
CSV_EXTENSIONS = (".csv",)
EXCEL_EXTENSIONS = (".xlsx", ".xls")
UTF_8_ENCODING = "utf-8"
CSV_SAMPLE_SIZE = 1024
DEFAULT_CSV_DELIMITER = ","


def _detect_file_type(file_path: Path) -> str:
    """Return 'csv' or 'excel' based on extension. Raises InvalidFileFormatError if unsupported."""
    ext = file_path.suffix.lower()
    if ext in CSV_EXTENSIONS:
        return "csv"
    if ext in EXCEL_EXTENSIONS:
        return "excel"
    raise InvalidFileFormatError(f"Unsupported file type: {ext}", file_path=file_path)


def get_file_columns(file_path: Path) -> List[str]:
    """
    Get the column names from a data file (CSV or Excel).

    Args:
        file_path: Path to the CSV or Excel file

    Returns:
        List of column names

    Raises:
        InvalidFileFormatError: If file type is unsupported or file cannot be read
    """
    file_type = _detect_file_type(file_path)

    if file_type == "csv":
        try:
            with open(file_path, "r", encoding=UTF_8_ENCODING) as f:
                sample = f.read(CSV_SAMPLE_SIZE)
                f.seek(0)
                try:
                    delimiter = csv.Sniffer().sniff(sample).delimiter if sample.strip() else DEFAULT_CSV_DELIMITER
                except Exception:
                    delimiter = DEFAULT_CSV_DELIMITER
                reader = csv.DictReader(f, delimiter=delimiter)
                if reader.fieldnames is not None:
                    return list(reader.fieldnames)
                return []
        except Exception as e:
            raise InvalidFileFormatError(f"Failed to read CSV file: {e}", file_path=file_path) from e

    if file_type == "excel":
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas and openpyxl are required to read Excel files. Install with: pip install pandas openpyxl"
            ) from e
        try:
            df = pd.read_excel(file_path, nrows=0)
            return list(df.columns)
        except Exception as e:
            raise InvalidFileFormatError(
                f"Failed to extract columns from Excel file: {e}", file_path=file_path
            ) from e

    return []
