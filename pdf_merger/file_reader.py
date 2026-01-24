"""
File reader module.
Handles reading CSV and Excel files with a unified interface.
"""

import csv
import pandas as pd
from pathlib import Path
from typing import Iterator, Dict, Any, List
from .exceptions import InvalidFileFormatError, MissingColumnError
from .enums import (
    EXCEL_FILE_EXTENSIONS,
    CSV_FILE_EXTENSIONS,
    FILE_TYPE_EXCEL,
    FILE_TYPE_CSV,
    DEFAULT_CSV_DELIMITER,
    CSV_SAMPLE_SIZE,
    PDF_FILE_EXTENSIONS,
    FILE_TYPE_PDF,
    UTF_8_ENCODING,
)

def detect_file_type(file_path: Path) -> str:
    """
    Detect the file type based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        One of: 'excel', 'csv', 'pdf'

    Raises:
        InvalidFileFormatError: If the file type is unsupported
    """
    file_extension = file_path.suffix.lower()
    if file_extension in EXCEL_FILE_EXTENSIONS:
        return FILE_TYPE_EXCEL
    elif file_extension in CSV_FILE_EXTENSIONS:
        return FILE_TYPE_CSV
    elif file_extension in PDF_FILE_EXTENSIONS:
        return FILE_TYPE_PDF
    raise InvalidFileFormatError(f"Unsupported file type: {file_extension}", file_path=file_path)


def _detect_csv_delimiter(file_path: Path) -> str:
    """
    Detect CSV delimiter from a file sample.

    Args:
        file_path: Path to the CSV file

    Returns:
        Detected delimiter character.
        Defaults to DEFAULT_CSV_DELIMITER if detection fails or file is empty.
    """
    try:
        with open(file_path, 'r', encoding=UTF_8_ENCODING) as csvfile:
            sample = csvfile.read(CSV_SAMPLE_SIZE)
            
            if not sample.strip():
                # Default to comma if file is empty
                return DEFAULT_CSV_DELIMITER
        
            return csv.Sniffer().sniff(sample).delimiter
    except Exception as e:
        raise InvalidFileFormatError(f"Failed to detect CSV delimiter for file {file_path}: {e}") from e


def read_csv(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Read a CSV file and yield rows as dictionaries.
    
    Args:
        file_path: Path to the CSV file
        
    Yields:
        Dictionary representing each row
        
    Raises:
        InvalidFileFormatError: If file cannot be read
    """
    try:
        delimiter = _detect_csv_delimiter(file_path)
        with open(file_path, 'r', encoding=UTF_8_ENCODING) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            for row in reader:
                yield row
    except Exception as e:
        raise InvalidFileFormatError(f"Failed to read CSV file {file_path}: {e}") from e


def read_excel(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Read an Excel file and yield rows as dictionaries.

    Args:
        file_path: Path to the Excel file

    Yields:
        Dictionary representing each row with string values

    Raises:
        InvalidFileFormatError: If the file cannot be read as an Excel file
    """
    try:
        df = pd.read_excel(file_path)
    except Exception as exc:
        raise InvalidFileFormatError(
            f"Failed to read Excel file {file_path}"
        ) from exc

    for record in df.fillna('').astype(str).to_dict(orient='records'):
        yield record



def read_data_file(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Read a data file (CSV or Excel) with a unified interface.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Yields:
        Dictionary representing each row
        
    Raises:
        ValueError: If file type is not supported
        ImportError: If required libraries are not installed for Excel files
    """
    file_type = detect_file_type(file_path)
    
    if file_type == FILE_TYPE_EXCEL:
        yield from read_excel(file_path)
    else:
        yield from read_csv(file_path)


def get_file_columns(file_path: Path) -> List[str]:
    """
    Get the column names from a data file.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Returns:
        List of column names
        
    Raises:
        ImportError: If required libraries are not installed for Excel files
        InvalidFileFormatError: If file cannot be read
    """
    file_type = detect_file_type(file_path)
    
    try:
        if file_type == FILE_TYPE_EXCEL:
            if pd is None:
                raise ImportError("pandas and openpyxl are required to read Excel files. Install with: pip install pandas openpyxl")
            df = pd.read_excel(file_path)
            return list(df.columns)
        else:
            delimiter = _detect_csv_delimiter(file_path)
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                return list(reader.fieldnames) if reader.fieldnames else []
    except ImportError:
        raise
    except Exception as e:
        raise InvalidFileFormatError(f"Failed to read file {file_path}: {e}") from e
