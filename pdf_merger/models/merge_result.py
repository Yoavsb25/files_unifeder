"""
Merge result model.
Represents the result of processing a merge job with detailed per-row results.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .enums import RowStatus
from .defaults import PERCENTAGE_MULTIPLIER
from ..utils.logging_utils import get_logger

logger = get_logger("pdf_merger.models.merge_result")


@dataclass
class RowResult:
    """
    Result of processing a single row.
    
    Attributes:
        row_index: Zero-based row index
        status: Processing status
        output_file: Path to the output merged PDF (if successful)
        files_found: List of source files found
        files_missing: List of serial numbers for which files were not found
        error_message: Error message if processing failed
        processing_time: Processing time in seconds (optional)
    """
    row_index: int
    status: RowStatus
    output_file: Optional[Path] = None
    files_found: List[Path] = field(default_factory=list)
    files_missing: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    
    def is_success(self) -> bool:
        """Check if row processing was successful."""
        return self.status == RowStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """Check if row processing failed."""
        return self.status == RowStatus.FAILED
    
    def is_skipped(self) -> bool:
        """Check if row was skipped."""
        return self.status == RowStatus.SKIPPED

    @classmethod
    def skipped(
        cls,
        row_index: int,
        error_message: Optional[str] = None,
        files_missing: Optional[List[str]] = None,
    ) -> "RowResult":
        """Factory: create a skipped row result."""
        return cls(row_index=row_index, status=RowStatus.SKIPPED, error_message=error_message, files_missing=files_missing or [])

    @classmethod
    def failed(
        cls,
        row_index: int,
        error_message: Optional[str] = None,
        files_found: Optional[List[Path]] = None,
        files_missing: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
    ) -> "RowResult":
        """Factory: create a failed row result."""
        return cls(
            row_index=row_index,
            status=RowStatus.FAILED,
            error_message=error_message,
            files_found=files_found or [],
            files_missing=files_missing or [],
            processing_time=processing_time,
        )

    @classmethod
    def success(
        cls,
        row_index: int,
        output_file: Path,
        files_found: List[Path],
        files_missing: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
    ) -> "RowResult":
        """Factory: create a successful row result (status SUCCESS or PARTIAL if files_missing)."""
        status = RowStatus.PARTIAL if (files_missing and len(files_missing) > 0) else RowStatus.SUCCESS
        return cls(
            row_index=row_index,
            status=status,
            output_file=output_file,
            files_found=files_found,
            files_missing=files_missing or [],
            processing_time=processing_time,
        )

    def __str__(self) -> str:
        status_str = self.status.value.upper()
        if self.output_file:
            return f"Row {self.row_index + 1}: {status_str} -> {self.output_file.name}"
        return f"Row {self.row_index + 1}: {status_str}"


@dataclass
class MergeResult:
    """
    Preferred result type for run_merge_job; includes per-row details and timing.
    Use ProcessingResult (core.result_types) only for legacy run_merge compatibility.

    Attributes:
        total_rows: Total number of rows processed
        successful_merges: Number of successfully merged rows
        failed_rows: List of row indices that failed
        skipped_rows: List of row indices that were skipped
        row_results: Detailed results for each row
        job_id: Optional job identifier
        total_processing_time: Total processing time in seconds (optional)
    """
    total_rows: int
    successful_merges: int
    failed_rows: List[int] = field(default_factory=list)
    skipped_rows: List[int] = field(default_factory=list)
    row_results: List[RowResult] = field(default_factory=list)
    job_id: Optional[str] = None
    total_processing_time: Optional[float] = None
    
    @classmethod
    def from_processing_result(cls, result, job_id: Optional[str] = None) -> 'MergeResult':
        """
        Create MergeResult from legacy ProcessingResult for backward compatibility.
        
        Args:
            result: ProcessingResult instance
            job_id: Optional job identifier
            
        Returns:
            MergeResult instance
        """
        return cls(
            total_rows=result.total_rows,
            successful_merges=result.successful_merges,
            failed_rows=result.failed_rows,
            skipped_rows=[],
            row_results=[],
            job_id=job_id
        )
    
    def add_row_result(self, row_result: RowResult) -> None:
        """
        Add a row result to the merge result.
        
        Args:
            row_result: RowResult instance
        """
        self.row_results.append(row_result)
        
        # Update counters
        if row_result.is_success():
            self.successful_merges += 1
        elif row_result.is_failed():
            self.failed_rows.append(row_result.row_index)
        elif row_result.is_skipped():
            self.skipped_rows.append(row_result.row_index)
    
    def get_success_rate(self) -> float:
        """
        Calculate success rate as a percentage.
        
        Returns:
            Success rate (0.0 to 100.0)
        """
        if self.total_rows == 0:
            return 0.0
        return (self.successful_merges / self.total_rows) * PERCENTAGE_MULTIPLIER
    
    def get_failed_row_results(self) -> List[RowResult]:
        """Get all failed row results."""
        return [r for r in self.row_results if r.is_failed()]
    
    def get_skipped_row_results(self) -> List[RowResult]:
        """Get all skipped row results."""
        return [r for r in self.row_results if r.is_skipped()]
    
    def __str__(self) -> str:
        return (
            f"MergeResult(total_rows={self.total_rows}, "
            f"successful={self.successful_merges}, "
            f"failed={len(self.failed_rows)}, "
            f"skipped={len(self.skipped_rows)})"
        )
