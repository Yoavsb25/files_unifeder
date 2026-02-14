"""
Merge job model.
Represents a complete merge job with metadata, source files, and configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .row import Row
from ..utils.logging_utils import get_logger
from ..core.constants import Constants

logger = get_logger("pdf_merger.models.merge_job")


@dataclass
class MergeJob:
    """
    Represents a complete merge job.
    
    Attributes:
        input_file: Path to the input CSV/Excel file
        source_folder: Path to the folder containing source files (PDF and Excel)
        output_folder: Path to the output folder for merged PDFs
        required_column: Name of the column containing serial numbers
        rows: List of Row objects to process
        job_id: Optional job identifier (for tracking/logging)
        metadata: Optional metadata dictionary for additional job information
    """
    input_file: Path
    source_folder: Path
    output_folder: Path
    required_column: str
    rows: List[Row]
    job_id: Optional[str] = None
    metadata: Optional[dict] = None
    
    @classmethod
    def create(
        cls,
        input_file: Path,
        source_folder: Path,
        output_folder: Path,
        required_column: str = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN,
        job_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> 'MergeJob':
        """
        Create a MergeJob instance.
        
        Args:
            input_file: Path to the input CSV/Excel file
            source_folder: Path to the folder containing source files
            output_folder: Path to the output folder
            required_column: Name of the column containing serial numbers
            job_id: Optional job identifier
            metadata: Optional metadata dictionary
            
        Returns:
            MergeJob instance
        """
        return cls(
            input_file=input_file,
            source_folder=source_folder,
            output_folder=output_folder,
            required_column=required_column,
            rows=[],
            job_id=job_id,
            metadata=metadata or {}
        )
    
    def add_row(self, row: Row) -> None:
        """
        Add a row to the job.
        
        Args:
            row: Row instance to add
        """
        self.rows.append(row)
    
    def add_rows(self, rows: List[Row]) -> None:
        """
        Add multiple rows to the job.
        
        Args:
            rows: List of Row instances to add
        """
        self.rows.extend(rows)
    
    def get_total_rows(self) -> int:
        """Get total number of rows in the job."""
        return len(self.rows)
    
    def get_rows_with_serial_numbers(self) -> List[Row]:
        """Get rows that have valid serial numbers."""
        return [row for row in self.rows if row.has_serial_numbers()]
    
    def __str__(self) -> str:
        return f"MergeJob(input_file={self.input_file.name}, rows={len(self.rows)})"
