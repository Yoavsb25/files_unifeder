"""
Job loader: load rows from file into a MergeJob.
Single place for file read and row loading; used by the orchestrator.
"""

from pathlib import Path
from typing import Optional

from .csv_excel_reader import read_data_file
from .types import ProgressCallback, PROGRESS_LOADING
from ..models import MergeJob, Row
from ..utils.logging_utils import get_logger
from ..utils.exceptions import InvalidFileFormatError, MissingColumnError, JobLoadError

logger = get_logger("pdf_merger.core.job_loader")


def load_job_from_file(
    input_file: Path,
    source_folder: Path,
    output_folder: Path,
    required_column: str,
    job_id: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> MergeJob:
    """
    Load input file and build a MergeJob with rows. Single implementation for the orchestrator.

    Returns a MergeJob with rows only when the file was read successfully (including empty file).
    On OSError, InvalidFileFormatError, or MissingColumnError, re-raises as-is.
    On any other exception during read, raises JobLoadError so callers can distinguish load
    failure from "zero rows."

    Args:
        input_file: Path to CSV or Excel file
        source_folder: Path to folder containing source files
        output_folder: Path to output folder for merged PDFs
        required_column: Name of the column containing serial numbers
        job_id: Optional job identifier
        on_progress: Optional callback (step, current, total, message)

    Returns:
        MergeJob with rows loaded (empty list if file has no data rows).

    Raises:
        OSError: On file I/O errors.
        InvalidFileFormatError: On unsupported or invalid file format.
        MissingColumnError: When required_column is missing.
        JobLoadError: On any other error during load (e.g. unexpected parse failure).
    """
    job = MergeJob.create(
        input_file=input_file,
        source_folder=source_folder,
        output_folder=output_folder,
        required_column=required_column,
        job_id=job_id,
    )
    if on_progress:
        on_progress(PROGRESS_LOADING, 0, 0, "Reading input file...")
    try:
        for row_index, row_data in enumerate(read_data_file(input_file), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except (OSError, InvalidFileFormatError, MissingColumnError):
        raise
    except Exception as e:
        logger.error("Unknown error during load: %s", e)
        raise JobLoadError(f"Failed to load job: {e}", path=input_file, cause=e) from e
    total_rows = job.get_total_rows()
    if on_progress:
        on_progress(PROGRESS_LOADING, total_rows, total_rows, f"Loaded {total_rows} rows")
    return job
