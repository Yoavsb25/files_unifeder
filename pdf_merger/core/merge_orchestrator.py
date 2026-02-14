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
from .job_loader import load_job_from_file
from .types import ProgressCallback
from .constants import Constants
from ..models import MergeResult
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

    **Deprecated.** Use :func:`run_merge_job` for new code. This function delegates to
    ``run_merge_job`` and returns ``MergeResult``. For legacy ``ProcessingResult`` use
    ``as_processing_result(result)`` from ``pdf_merger.core.result_types``.
    Deprecated entry points will be removed in version 2.0. See DEPRECATION.md.

    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        on_progress: Optional callback (step, current, total, message) for progress updates

    Returns:
        MergeResult with detailed processing results
    """
    import warnings

    warnings.warn(
        "run_merge is deprecated; use run_merge_job instead. Will be removed in 2.0.",
        DeprecationWarning,
        stacklevel=2,
    )
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

    job = load_job_from_file(
        input_file=input_file,
        source_folder=pdf_dir,
        output_folder=output_dir,
        required_column=required_column,
        job_id=job_id,
        on_progress=on_progress,
    )
    result = process_job(job, fail_on_ambiguous=fail_on_ambiguous, on_progress=on_progress)
    
    logger.info(f"Merge job {job_id or 'default'} completed")
    logger.info(f"  Total rows: {result.total_rows}")
    logger.info(f"  Successful: {result.successful_merges}")
    logger.info(f"  Failed: {len(result.failed_rows)}")
    logger.info(f"  Skipped: {len(result.skipped_rows)}")
    
    return result
