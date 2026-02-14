"""
Validation utilities module.
Handles validation of files, folders, and paths.

Validation API: validate_file, validate_folder, validate_paths raise
FileNotFoundError, MissingColumnError, InvalidFileFormatError, ValidationError.
Used by UI (inline errors), orchestrator, and config loading. Config is valid
at process_job/run_merge_job entry; backend can assume valid paths and column.

Validation Strategy:
- Critical validations (file/folder/paths): Raise exceptions - these are pre-conditions
- Data validations (serial numbers): Return bool - allow graceful degradation
"""

from pathlib import Path
from .logging_utils import get_logger
from .exceptions import MissingColumnError, FileNotFoundError, ValidationError, InvalidFileFormatError
from ..core.constants import Constants
from ..core.csv_excel_reader import get_file_columns

logger = get_logger("pdf_merger.utils.validators")

# Module-level constants (single source: core.constants.Constants)
SERIAL_NUMBER_PREFIX = Constants.SERIAL_NUMBER_PREFIX
SERIAL_NUMBER_PREFIX_LOWER = Constants.SERIAL_NUMBER_PREFIX_LOWER

def validate_serial_number(serial_number: str) -> bool:
    """
    Validate the structure of a serial number.
    
    Args:
        serial_number: a single string of a serial number (e.g. "GRNW_000103851")
        
    Returns:
        True if valid, False otherwise
    """
    if not serial_number or not serial_number.strip():
        return False

    if not serial_number.startswith(SERIAL_NUMBER_PREFIX) and not serial_number.startswith(SERIAL_NUMBER_PREFIX_LOWER):
        return False

    suffix = serial_number.split('_', 1)[-1]
    if not suffix.isdigit():
        return False
        
    return True


def validate_folder(folder_path: Path, folder_type: str = "Folder") -> None:
    """
    Validate that a folder exists and is a directory.
    
    Args:
        folder_path: Path to validate
        folder_type: Type description for error messages (e.g., "Source", "Output")
        
    Raises:
        FileNotFoundError: If folder doesn't exist or is not a directory
    """
    if not folder_path.exists():
        logger.error(f"{folder_type} folder not found: {folder_path}")
        raise FileNotFoundError(folder_path, file_type=f"{folder_type} folder")
    
    if not folder_path.is_dir():
        logger.error(f"{folder_path} is not a directory")
        raise FileNotFoundError(folder_path, file_type=f"{folder_type} (not a directory)")


def validate_file(file_path: Path, required_column: str = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN) -> None:
    """
    Validate that a data file exists and has the required column.
    
    Args:
        file_path: Path to the file to validate
        required_column: Name of the required column (default: 'serial_numbers')
        
    Raises:
        FileNotFoundError: If file doesn't exist
        MissingColumnError: If required column is missing
        InvalidFileFormatError: If file cannot be read (wrapped from exceptions)
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(file_path, file_type="Data file")
    
    try:
        columns = get_file_columns(file_path)
        
        if required_column not in columns:
            logger.error(f"'{required_column}' column not found in file.")
            logger.error(f"Available columns: {', '.join(columns)}")
            raise MissingColumnError(required_column, columns, file_path)
    except (MissingColumnError, FileNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise InvalidFileFormatError(f"Error reading file: {e}", file_path=file_path) from e


def validate_paths(file_path: Path, source_folder: Path, output_folder: Path,
                   required_column: str = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN) -> None:
    """
    Validate all paths needed for processing.
    
    Args:
        file_path: Path to the data file (CSV/Excel)
        source_folder: Path to folder containing PDF files
        output_folder: Path to output folder
        required_column: Name of the required column
        
    Raises:
        FileNotFoundError: If file or folder doesn't exist
        MissingColumnError: If required column is missing from file
        ValidationError: If output folder parent doesn't exist
    """
    # Validate file (raises FileNotFoundError or MissingColumnError)
    validate_file(file_path, required_column)
    
    # Validate source folder (raises FileNotFoundError)
    validate_folder(source_folder, "Source")
    
    # Validate output folder parent exists (if output folder is not root)
    if output_folder.parent != output_folder:
        if not output_folder.parent.exists():
            logger.error(f"Parent directory of output folder does not exist: {output_folder.parent}")
            raise ValidationError(
                f"Parent directory of output folder does not exist: {output_folder.parent}",
                field="output_folder"
            )
