"""
Merge orchestrator module.

- Orchestrator: UI-facing API and job construction (run_merge_job). Loads rows from file and builds MergeJob.
- Row creation from raw data (Row.from_raw_data) lives here; processor only receives MergeJob with rows.
- Do not add job execution or row-level logic here—those belong in merge_processor.
- Processor (merge_processor): job execution and row-level logic (process_job, process_row_with_models); do not add UI-facing API or row loading from file there.
"""

from pathlib import Path
from typing import Optional

from .merge_processor import process_job
from .job_loader import load_job_from_file
from .types import ProgressCallback
from .constants import Constants
from ..models import MergeResult, RowResult
from ..utils.logging_utils import get_logger
from ..utils.exceptions import JobLoadError

logger = get_logger("pdf_merger.core.merge_orchestrator")


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
        fail_on_ambiguous: If True, raise on ambiguous file matches (default True)
        on_progress: Optional callback (step, current, total, message) for progress updates

    Returns:
        MergeResult with detailed processing results

    Note:
        on_progress is invoked from the processing thread; schedule UI updates on the main thread if needed.
    """
    logger.info(f"Starting merge job {job_id or 'default'}")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  Source directory: {pdf_dir}")
    logger.info(f"  Output directory: {output_dir}")

    try:
        job = load_job_from_file(
            input_file=input_file,
            source_folder=pdf_dir,
            output_folder=output_dir,
            required_column=required_column,
            job_id=job_id,
            on_progress=on_progress,
        )
    except JobLoadError as e:
        logger.error("Job load failed: %s", e)
        result = MergeResult(total_rows=0, successful_merges=0, job_id=job_id)
        result.add_row_result(
            RowResult.failed(row_index=0, error_message=str(e))
        )
        return result

    result = process_job(job, fail_on_ambiguous=fail_on_ambiguous, on_progress=on_progress)

    logger.info(f"Merge job {job_id or 'default'} completed")
    logger.info(f"  Total rows: {result.total_rows}")
    logger.info(f"  Successful: {result.successful_merges}")
    logger.info(f"  Failed: {len(result.failed_rows)}")
    logger.info(f"  Skipped: {len(result.skipped_rows)}")
    
    return result
