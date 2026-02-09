"""
Merge processor module.
Main orchestration logic for processing files and merging PDFs.
Depends on operations.run_merge_for_row only (facade); no direct dependency on concrete I/O modules.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..operations import run_merge_for_row
from ..operations.protocols import MergeOperations
from .csv_excel_reader import read_data_file
from ..utils.logging_utils import get_logger
from ..utils.exceptions import PDFMergerError
from .constants import Constants
from ..models import Row, MergeJob, MergeResult, RowResult, RowStatus
from ..utils.validators import validate_serial_number
from .serial_number_parser import (
    split_serial_numbers,
    deduplicate_serial_numbers,
    normalize_serial_number,
)
from ..observability import get_metrics_collector

logger = get_logger("merge_processor")

# Module-level constants
OUTPUT_FILENAME_PATTERN = Constants.OUTPUT_FILENAME_PATTERN
DEFAULT_SERIAL_NUMBERS_COLUMN = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
BYTES_PER_MB = Constants.BYTES_PER_MB


@dataclass
class ProcessingResult:
    """
    Result of processing a file.
    
    Note: This class is kept for backward compatibility.
    New code should use MergeResult from models package.
    """
    total_rows: int
    successful_merges: int
    failed_rows: List[int]
    
    def __str__(self) -> str:
        return (f"Total rows processed: {self.total_rows}\n"
                f"Successfully merged PDFs: {self.successful_merges}\n"
                f"Failed rows: {len(self.failed_rows)}")


def process_row(
    row_index: int,
    serial_numbers_str: str,
    source_folder: Path,
    output_folder: Path,
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN,
) -> bool:
    """
    Process a single row: find PDFs and Excel files, convert Excel to PDF, and merge them.

    Note: This function is kept for backward compatibility and testing.
    New code should use process_row_with_models() with domain models.

    Args:
        row_index: Index of the row (0-based, for naming output file)
        serial_numbers_str: Comma-separated filenames from the serial_numbers column
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        required_column: Name of the column containing serial numbers (default: serial_numbers)

    Returns:
        True if successful, False otherwise
    """
    raw_data = {required_column: serial_numbers_str}
    row = Row.from_raw_data(row_index, raw_data, required_column)
    result = run_merge_for_row(
        row, source_folder, output_folder, fail_on_ambiguous=False
    )
    return result.is_success() or result.status == RowStatus.PARTIAL


def process_row_with_models(
    row: Row,
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = True,
    merge_operations: Optional[MergeOperations] = None,
) -> RowResult:
    """
    Process a single row using domain models: find PDFs and Excel files, convert Excel to PDF, and merge them.

    Args:
        row: Row instance to process
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        merge_operations: Optional I/O implementation for tests (default: real filesystem)

    Returns:
        RowResult with processing details
    """
    metrics = get_metrics_collector()
    result = run_merge_for_row(
        row,
        source_folder,
        output_folder,
        fail_on_ambiguous=fail_on_ambiguous,
        operations=merge_operations,
    )
    # Record metrics from result
    if result.status == RowStatus.SKIPPED:
        metrics.record_counter("rows_skipped", tags={"reason": str(result.error_message or "unknown")[:50]})
    elif result.is_success() or result.status == RowStatus.PARTIAL:
        metrics.record_counter("rows_successful")
        if result.processing_time is not None:
            metrics.record_timer("row_processing_time", result.processing_time)
        if result.output_file and result.output_file.exists():
            try:
                file_size_mb = result.output_file.stat().st_size / BYTES_PER_MB
                metrics.record_gauge("output_file_size_mb", file_size_mb)
            except Exception:
                pass
    else:
        metrics.record_counter("rows_failed", tags={"reason": "merge_failed"})
        if result.processing_time is not None:
            metrics.record_timer("row_processing_time", result.processing_time)
    for _ in result.files_found:
        metrics.record_counter("files_found")
    for _ in result.files_missing:
        metrics.record_counter("files_missing")
    return result


def process_job(
    job: MergeJob,
    fail_on_ambiguous: bool = True,
    merge_operations: Optional[MergeOperations] = None,
) -> MergeResult:
    """
    Process a merge job using domain models.

    Args:
        job: MergeJob instance to process
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        merge_operations: Optional I/O implementation for tests (default: real filesystem)

    Returns:
        MergeResult with detailed processing results
    """
    job.output_folder.mkdir(parents=True, exist_ok=True)
    
    result = MergeResult(
        total_rows=job.get_total_rows(),
        successful_merges=0,
        job_id=job.job_id,
    )
    
    start_time = time.time()
    metrics = get_metrics_collector()
    metrics.record_counter("jobs_started")
    
    try:
        for row in job.rows:
            row_result = process_row_with_models(
                row,
                job.source_folder,
                job.output_folder,
                fail_on_ambiguous=fail_on_ambiguous,
                merge_operations=merge_operations,
            )
            result.add_row_result(row_result)
        
        result.total_processing_time = time.time() - start_time
        metrics.record_timer("job_processing_time", result.total_processing_time)
        metrics.record_counter("jobs_completed")
        metrics.record_gauge("job_success_rate", result.get_success_rate())
        
        logger.info(f"Job {job.job_id or 'default'} completed: {result}")
        return result
        
    except PDFMergerError as e:
        logger.error(f"PDF Merger error: {e}")
        metrics.record_counter("jobs_failed", tags={"error_type": "PDFMergerError"})
        result.total_processing_time = time.time() - start_time
        return result
    except ValueError as e:
        # Ambiguous match error
        logger.error(f"Ambiguous match error: {e}")
        metrics.record_counter("jobs_failed", tags={"error_type": "AmbiguousMatch"})
        result.total_processing_time = time.time() - start_time
        return result
    except Exception as e:
        logger.error(f"Unexpected error processing job: {e}")
        metrics.record_counter("jobs_failed", tags={"error_type": "UnexpectedError"})
        result.total_processing_time = time.time() - start_time
        return result


def process_file(
    file_path: Path,
    source_folder: Path,
    output_folder: Path,
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN,
    fail_on_ambiguous: bool = True,
) -> ProcessingResult:
    """
    Process an entire data file and merge PDFs and Excel files for each row.

    Note: This function is kept for backward compatibility.
    New code should use process_job() with MergeJob domain model.

    Args:
        file_path: Path to the CSV or Excel file
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        required_column: Name of the column containing serial numbers
        fail_on_ambiguous: If True, raise on ambiguous file matches (default: True)

    Returns:
        ProcessingResult with statistics about the processing
    """
    job = MergeJob.create(
        input_file=file_path,
        source_folder=source_folder,
        output_folder=output_folder,
        required_column=required_column,
    )

    try:
        for row_index, row_data in enumerate(read_data_file(file_path), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return ProcessingResult(total_rows=0, successful_merges=0, failed_rows=[])

    merge_result = process_job(job, fail_on_ambiguous=fail_on_ambiguous)

    return ProcessingResult(
        total_rows=merge_result.total_rows,
        successful_merges=merge_result.successful_merges,
        failed_rows=merge_result.failed_rows,
    )
