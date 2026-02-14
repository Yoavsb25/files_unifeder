"""
Serial number parsing (re-export from utils).
Backward-compatible re-export so core and tests can keep importing from here.
Implementation lives in utils.serial_number_parser so Row and models need not depend on core.
"""

from ..utils.serial_number_parser import (
    split_serial_numbers,
    deduplicate_serial_numbers,
    normalize_serial_number,
    SERIAL_NUMBER_SEPARATOR,
    SERIAL_NUMBER_PREFIX,
    SERIAL_NUMBER_PREFIX_LOWER,
)

__all__ = [
    "split_serial_numbers",
    "deduplicate_serial_numbers",
    "normalize_serial_number",
    "SERIAL_NUMBER_SEPARATOR",
    "SERIAL_NUMBER_PREFIX",
    "SERIAL_NUMBER_PREFIX_LOWER",
]
