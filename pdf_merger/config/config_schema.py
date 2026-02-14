"""
Configuration schema and validation.
Provides validation functions for application configuration.
All AppConfig fields are validated here; invalid values are coerced to defaults with a log warning.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from ..core.constants import Constants
from ..utils.logging_utils import get_logger

logger = get_logger("pdf_merger.config.config_schema")


def validate_input_file(value: Optional[str]) -> Optional[str]:
    """
    Validate input file path.

    Args:
        value: Input file path string

    Returns:
        Validated path string or None

    Raises:
        ValueError: If path is invalid
    """
    if value is None or value == "":
        return None

    path = Path(value)
    if not path.exists():
        raise ValueError(f"Input file does not exist: {value}")

    if not path.is_file():
        raise ValueError(f"Input file is not a file: {value}")

    return str(path.resolve())


def validate_source_dir(value: Optional[str]) -> Optional[str]:
    """
    Validate source directory path.

    Args:
        value: Source directory path string

    Returns:
        Validated path string or None

    Raises:
        ValueError: If path is invalid
    """
    if value is None or value == "":
        return None

    path = Path(value)
    if not path.exists():
        raise ValueError(f"Source directory does not exist: {value}")

    if not path.is_dir():
        raise ValueError(f"Source directory is not a directory: {value}")

    return str(path.resolve())


def validate_output_dir(value: Optional[str]) -> Optional[str]:
    """
    Validate output directory path (will be created if it doesn't exist).

    Args:
        value: Output directory path string

    Returns:
        Validated path string or None

    Raises:
        ValueError: If path is invalid
    """
    if value is None or value == "":
        return None

    path = Path(value)
    # Output directory can be created, so we just validate the parent exists
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {value}")

    # Try to create parent if needed
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create output directory: {e}")

    return str(path.resolve())


def validate_column(value: Optional[str]) -> str:
    """
    Validate column name.

    Args:
        value: Column name string

    Returns:
        Validated column name

    Raises:
        ValueError: If column name is invalid
    """
    if value is None or value == "":
        return Constants.DEFAULT_SERIAL_NUMBERS_COLUMN

    # Column names should be non-empty strings
    if not isinstance(value, str) or len(value.strip()) == 0:
        raise ValueError(f"Column name must be a non-empty string: {value}")

    return value.strip()


def _validate_boolean(value: Any, key: str, default: bool) -> bool:
    """Coerce value to bool; log and return default if invalid."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        if lower in ("false", "0", "no", "off"):
            return False
    logger.warning(f"Invalid {key} in config: expected boolean, got {type(value).__name__}; using default {default}")
    return default


def validate_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate entire configuration dictionary.
    All AppConfig fields (paths, column, observability, fail_on_ambiguous_matches) are validated.
    Invalid values are logged and coerced to defaults.

    Args:
        data: Configuration dictionary

    Returns:
        Validated configuration dictionary
    """
    validated: Dict[str, Any] = {}

    # Validate input_file
    if "input_file" in data:
        try:
            validated["input_file"] = validate_input_file(data["input_file"])
        except ValueError as e:
            logger.warning(f"Invalid input_file in config: {e}")
            validated["input_file"] = None

    # Validate pdf_dir (source_dir)
    if "pdf_dir" in data:
        try:
            validated["pdf_dir"] = validate_source_dir(data["pdf_dir"])
        except ValueError as e:
            logger.warning(f"Invalid pdf_dir in config: {e}")
            validated["pdf_dir"] = None

    # Also handle source_dir alias
    if "source_dir" in data and "pdf_dir" not in validated:
        try:
            validated["pdf_dir"] = validate_source_dir(data["source_dir"])
        except ValueError as e:
            logger.warning(f"Invalid source_dir in config: {e}")
            validated["pdf_dir"] = None

    # Validate output_dir
    if "output_dir" in data:
        try:
            validated["output_dir"] = validate_output_dir(data["output_dir"])
        except ValueError as e:
            logger.warning(f"Invalid output_dir in config: {e}")
            validated["output_dir"] = None

    # Validate required_column
    if "required_column" in data:
        try:
            validated["required_column"] = validate_column(data["required_column"])
        except ValueError as e:
            logger.warning(f"Invalid required_column in config: {e}")
            validated["required_column"] = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    else:
        validated["required_column"] = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN

    # Observability and matching: validate booleans when present
    if "metrics_enabled" in data:
        validated["metrics_enabled"] = _validate_boolean(
            data["metrics_enabled"], "metrics_enabled", default=True
        )
    if "telemetry_enabled" in data:
        validated["telemetry_enabled"] = _validate_boolean(
            data["telemetry_enabled"], "telemetry_enabled", default=False
        )
    if "crash_reporting_enabled" in data:
        validated["crash_reporting_enabled"] = _validate_boolean(
            data["crash_reporting_enabled"], "crash_reporting_enabled", default=False
        )
    if "fail_on_ambiguous_matches" in data:
        validated["fail_on_ambiguous_matches"] = _validate_boolean(
            data["fail_on_ambiguous_matches"], "fail_on_ambiguous_matches", default=True
        )

    return validated
