"""
Data parsing module.
Handles parsing serial numbers from strings.
"""

from typing import List, Set, Optional
from .constants import Constants

# Module-level constants
SERIAL_NUMBER_SEPARATOR = Constants.SERIAL_NUMBER_SEPARATOR
SERIAL_NUMBER_PREFIX = Constants.SERIAL_NUMBER_PREFIX
SERIAL_NUMBER_PREFIX_LOWER = Constants.SERIAL_NUMBER_PREFIX_LOWER

def split_serial_numbers(serial_numbers_str: str) -> List[str]:
    """
    Split serial numbers from a string into a list of strings according to a known separator.
    
    Args:
        serial_numbers_str: String containing serial numbers separated by a known separator
        
    Returns:
        List of serial numbers (stripped of whitespace)
    """
    if not serial_numbers_str or not serial_numbers_str.strip():
        return []
    
    serial_numbers = [s.strip() for s in serial_numbers_str.split(SERIAL_NUMBER_SEPARATOR)]

    return [s for s in serial_numbers if s]


def normalize_serial_number(serial_number: str, to_uppercase: bool = True) -> str:
    """
    Normalize a serial number to a standard format.
    Only normalizes the prefix (GRNW_/grnw_), leaving the numeric suffix unchanged.
    
    Args:
        serial_number: Serial number to normalize
        to_uppercase: If True, convert prefix to uppercase; if False, convert to lowercase
        
    Returns:
        Normalized serial number string
    """
    if not serial_number:
        return serial_number
    
    normalized = serial_number.strip()
    
    if to_uppercase:
        if normalized.startswith(SERIAL_NUMBER_PREFIX_LOWER):
            normalized = SERIAL_NUMBER_PREFIX + normalized[len(SERIAL_NUMBER_PREFIX_LOWER):]
    else:
        if normalized.startswith(SERIAL_NUMBER_PREFIX):
            normalized = SERIAL_NUMBER_PREFIX_LOWER + normalized[len(SERIAL_NUMBER_PREFIX):]
    
    return normalized


def deduplicate_serial_numbers(serial_numbers: List[str], preserve_order: bool = True) -> List[str]:
    """
    Remove duplicate serial numbers from a list.
    
    Args:
        serial_numbers: List of serial number strings
        preserve_order: If True, preserve the order of first occurrence
        
    Returns:
        List of unique serial numbers
    """
    if not serial_numbers:
        return []
    
    if preserve_order:
        seen: Set[str] = set()
        result = []
        for serial in serial_numbers:
            if serial and serial not in seen:
                seen.add(serial)
                result.append(serial)
        return result
    else:
        return list(set(serial_numbers))
