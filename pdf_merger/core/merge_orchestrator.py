"""
Merge orchestrator module.
Wrapper around process_file and process_job for UI consumption.
"""

from pathlib import Path
from typing import Callable, Optional

from .merge_processor import process_file, process_job, ProcessingResult
from ..models import MergeJob, MergeResult, Row
from .csv_excel_reader import read_data_file
from .constants import Constants
from ..utils.logging_utils import get_logger

logger = get_logger("core.merge_orchestrator")

# Module-level constants
DEFAULT_SERIAL_NUMBERS_COLUMN = Constants.GOLDFARB_SERIAL_NUMBER_COLUMN


def run_merge(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: Optional[str] = None,
    on_progress: Optional[Callable[[str, int, int, str], None]] = None,
) -> ProcessingResult:
    """
    Run the merge operation (legacy interface).

    Note: This function is kept for backward compatibility.
    New code should use run_merge_job() with domain models.

    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        on_progress: Optional callback (step, current, total, message) for progress updates

    Returns:
        ProcessingResult with statistics
    """
    column = required_column or DEFAULT_SERIAL_NUMBERS_COLUMN

    logger.info(f"Starting merge operation")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  Source directory: {pdf_dir}")
    logger.info(f"  Output directory: {output_dir}")

    try:
        result = process_file(
            file_path=input_file,
            source_folder=pdf_dir,
            output_folder=output_dir,
            required_column=column,
            on_progress=on_progress,
        )
        
        logger.info(f"Merge operation completed")
        logger.info(f"  Total rows: {result.total_rows}")
        logger.info(f"  Successful: {result.successful_merges}")
        logger.info(f"  Failed: {len(result.failed_rows)}")
        
        return result
    except Exception as e:
        logger.error(f"Error during merge operation: {e}")
        raise


def run_merge_job(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN,
    job_id: Optional[str] = None,
    fail_on_ambiguous: bool = True,
    on_progress: Optional[Callable[[str, int, int, str], None]] = None,
) -> MergeResult:
    """
    Run the merge operation using domain models.
    
    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        job_id: Optional job identifier for tracking
        
    Returns:
        MergeResult with detailed processing results
    """
    logger.info(f"Starting merge job {job_id or 'default'}")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  Source directory: {pdf_dir}")
    logger.info(f"  Output directory: {output_dir}")
    
    # Create merge job
    job = MergeJob.create(
        input_file=input_file,
        source_folder=pdf_dir,
        output_folder=output_dir,
        required_column=required_column,
        job_id=job_id
    )
    
    # Load rows from file
    if on_progress:
        on_progress("loading", 0, 0, "Reading input file...")
    try:
        for row_index, row_data in enumerate(read_data_file(input_file), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return MergeResult(
            total_rows=0,
            successful_merges=0,
            job_id=job_id
        )
    total_rows = job.get_total_rows()
    if on_progress:
        on_progress("loading", total_rows, total_rows, f"Loaded {total_rows} rows")

    # Process job
    result = process_job(job, fail_on_ambiguous=fail_on_ambiguous, on_progress=on_progress)
    
    logger.info(f"Merge job {job_id or 'default'} completed")
    logger.info(f"  Total rows: {result.total_rows}")
    logger.info(f"  Successful: {result.successful_merges}")
    logger.info(f"  Failed: {len(result.failed_rows)}")
    logger.info(f"  Skipped: {len(result.skipped_rows)}")
    
    return result
