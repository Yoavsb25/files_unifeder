"""
Merge orchestrator module.

Orchestrator: UI-facing API and job construction (run_merge, run_merge_job);
loads rows from file and builds MergeJob. Orchestrator owns row creation from
raw data (Row.from_raw_data); processor only receives MergeJob with rows. Do not
add job execution or row-level logic here—those belong in merge_processor. Processor (merge_processor): job
execution and row-level logic (process_job, process_row_with_models); do not
add UI-facing API or row loading from file here.
"""

from pathlib import Path
from typing import Optional

from .merge_processor import process_job
from .types import ProgressCallback, PROGRESS_LOADING
from ..models import MergeJob, MergeResult, Row
from .csv_excel_reader import read_data_file
from .constants import Constants
from ..utils.logging_utils import get_logger

logger = get_logger("pdf_merger.core.merge_orchestrator")


def run_merge(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> MergeResult:
    """
    Run the merge operation (legacy entry point; same pipeline as run_merge_job).

    Prefer run_merge_job() for new code. This function delegates to run_merge_job and returns
    MergeResult. For legacy ProcessingResult, use as_processing_result(result) from core.result_types.

    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        on_progress: Optional callback (step, current, total, message) for progress updates

    Returns:
        MergeResult with detailed processing results
    """
    column = required_column or Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    return run_merge_job(
        input_file=input_file,
        pdf_dir=pdf_dir,
        output_dir=output_dir,
        required_column=column,
        on_progress=on_progress,
    )


def run_merge_job(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN,
    job_id: Optional[str] = None,
    fail_on_ambiguous: bool = True,
    on_progress: Optional[ProgressCallback] = None,
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
        on_progress(PROGRESS_LOADING, 0, 0, "Reading input file...")
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
        on_progress(PROGRESS_LOADING, total_rows, total_rows, f"Loaded {total_rows} rows")

    # Process job
    result = process_job(job, fail_on_ambiguous=fail_on_ambiguous, on_progress=on_progress)
    
    logger.info(f"Merge job {job_id or 'default'} completed")
    logger.info(f"  Total rows: {result.total_rows}")
    logger.info(f"  Successful: {result.successful_merges}")
    logger.info(f"  Failed: {len(result.failed_rows)}")
    logger.info(f"  Skipped: {len(result.skipped_rows)}")
    
    return result
