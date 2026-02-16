"""
Row data model.
Represents a single row from the input data file.
"""

from dataclasses import dataclass
from typing import List, Optional

from ..utils.logging_utils import get_logger
from ..utils.validators import validate_serial_number
from ..core.serial_number_parser import (
    split_serial_numbers,
    deduplicate_serial_numbers,
    normalize_serial_number
)

logger = get_logger("models.row")


@dataclass
class Row:
    """
    Represents a single row from the input data file.
    
    Attributes:
        row_index: Zero-based row index (for naming output files)
        raw_data: Raw row data as dictionary (column name -> value)
        serial_numbers_str: Raw serial numbers string from the specified column
        serial_numbers: Parsed and validated serial numbers list
        required_column: Name of the column containing serial numbers
        output_name: Optional custom name for merged output file (from output_name_column)
    """
    row_index: int
    raw_data: dict
    serial_numbers_str: str
    serial_numbers: List[str]
    required_column: str
    output_name: Optional[str] = None
    
    @classmethod
    def from_raw_data(
        cls,
        row_index: int,
        raw_data: dict,
        required_column: str,
        output_name_column: Optional[str] = None,
    ) -> 'Row':
        """
        Create a Row from raw data dictionary.
        
        Args:
            row_index: Zero-based row index
            raw_data: Raw row data dictionary
            required_column: Name of the column containing serial numbers
            output_name_column: Optional column name for custom merged output filename
            
        Returns:
            Row instance with parsed and validated serial numbers
        """
        serial_numbers_str = raw_data.get(required_column, '')
        
        # Parse and validate serial numbers
        all_serial_numbers = split_serial_numbers(serial_numbers_str)
        valid_serial_numbers = []
        
        for serial_number in all_serial_numbers:
            if validate_serial_number(serial_number):
                valid_serial_numbers.append(serial_number)
            else:
                logger.warning(f"Row {row_index + 1}: Invalid serial number format: {serial_number}")
        
        # Deduplicate and normalize
        unique_serial_numbers = deduplicate_serial_numbers(valid_serial_numbers, preserve_order=True)
        normalized_serial_numbers = [
            normalize_serial_number(s, to_uppercase=True) 
            for s in unique_serial_numbers
        ]
        
        output_name = None
        if output_name_column and output_name_column.strip():
            raw_output_name = raw_data.get(output_name_column, '').strip()
            output_name = raw_output_name or None
        
        return cls(
            row_index=row_index,
            raw_data=raw_data,
            serial_numbers_str=serial_numbers_str,
            serial_numbers=normalized_serial_numbers,
            required_column=required_column,
            output_name=output_name,
        )
    
    def has_serial_numbers(self) -> bool:
        """Check if row has any valid serial numbers."""
        return len(self.serial_numbers) > 0
    
    def __str__(self) -> str:
        return f"Row {self.row_index + 1}: {len(self.serial_numbers)} serial number(s)"
