"""
Merge processor module.
Job execution and row-level logic (process_job, process_row_with_models).
Do not add UI-facing API or row loading from file here—those belong in
merge_orchestrator. When on_progress is provided, row-level logs are
suppressed (quiet=True) to avoid duplicate or out-of-order messages.
Log levels: user-visible milestones = info, per-row detail = debug.
"""

import time
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from .types import ProgressCallback, PROGRESS_LOADING, PROGRESS_PROCESSING
from .row_pipeline import run_row_pipeline, RowPipelineResult
from .csv_excel_reader import read_data_file
from ..utils.logging_utils import get_logger
from ..utils.exceptions import PDFMergerError
from .constants import Constants
from ..models import Row, MergeJob, MergeResult, RowResult, RowStatus
from ..utils.validators import validate_serial_number
from .serial_number_parser import (
    split_serial_numbers,
    deduplicate_serial_numbers,
    normalize_serial_number
)
from ..observability import get_metrics_collector
from .result_types import ProcessingResult

if TYPE_CHECKING:
    from ..observability import MetricsRecorder

logger = get_logger("pdf_merger.core.merge_processor")

EXCEL_FILE_EXTENSIONS = Constants.EXCEL_FILE_EXTENSIONS
BYTES_PER_MB = Constants.BYTES_PER_MB
MAX_MISSING_TO_LIST = Constants.MAX_MISSING_TO_LIST


def process_row(row_index: int, serial_numbers_str: str, source_folder: Path, 
                output_folder: Path) -> bool:
    """
    Process a single row: find PDFs and Excel files, convert Excel to PDF, and merge them.
    
    Note: This function is kept for backward compatibility and testing.
    New code should use process_row_with_models() with domain models.
    
    Args:
        row_index: Index of the row (0-based, for naming output file)
        serial_numbers_str: Comma-separated filenames from the serial_numbers column
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        
    Returns:
        True if successful, False otherwise
    """
    all_serial_numbers = split_serial_numbers(serial_numbers_str)
    if not all_serial_numbers:
        logger.warning(f"Row {row_index + 1}: No serial numbers found, skipping...")
        return False
    
    valid_serial_numbers = []
    for serial_number in all_serial_numbers:
        if validate_serial_number(serial_number):
            valid_serial_numbers.append(serial_number)
            continue
        logger.warning(f"Row {row_index + 1}: Invalid serial number format: {serial_number}")
        
    unique_serial_numbers = deduplicate_serial_numbers(valid_serial_numbers, preserve_order=True)
    normalized_serial_numbers = [normalize_serial_number(s, to_uppercase=True) for s in unique_serial_numbers]
    
    if not normalized_serial_numbers:
        logger.warning(f"Row {row_index + 1}: No valid serial numbers after filtering, skipping...")
        return False
    
    logger.info(f"Row {row_index + 1}: Processing serial numbers: {', '.join(normalized_serial_numbers)}")
    pipeline = run_row_pipeline(
        row_index, normalized_serial_numbers, source_folder, output_folder, fail_on_ambiguous=False, quiet=False
    )
    if not pipeline.success and not pipeline.source_files:
        logger.warning(f"Row {row_index + 1}: No files found for any serial numbers, skipping...")
    elif not pipeline.success and pipeline.error_message == "No PDF files available for merging":
        logger.warning(f"Row {row_index + 1}: No PDF files to merge (conversions may have failed), skipping...")
    return pipeline.success


def _pipeline_result_to_row_result(
    row_index: int,
    pipeline: RowPipelineResult,
    processing_time: float,
) -> RowResult:
    """Map RowPipelineResult to RowResult (single place for pipeline -> result mapping)."""
    if not pipeline.source_files:
        return RowResult(
            row_index=row_index,
            status=RowStatus.SKIPPED,
            files_missing=pipeline.missing,
            error_message=pipeline.error_message or "No source files found",
        )
    if pipeline.error_message == "No PDF files available for merging":
        return RowResult(
            row_index=row_index,
            status=RowStatus.FAILED,
            files_found=pipeline.source_files,
            files_missing=pipeline.missing,
            error_message=pipeline.error_message,
        )
    if pipeline.success:
        status = RowStatus.PARTIAL if pipeline.missing else RowStatus.SUCCESS
        return RowResult(
            row_index=row_index,
            status=status,
            output_file=pipeline.output_path,
            files_found=pipeline.source_files,
            files_missing=pipeline.missing,
            processing_time=processing_time,
        )
    return RowResult(
        row_index=row_index,
        status=RowStatus.FAILED,
        files_found=pipeline.source_files,
        files_missing=pipeline.missing,
        error_message=pipeline.error_message or "Failed to merge PDFs",
        processing_time=processing_time,
    )


def process_row_with_models(
    row: Row,
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = True,
    quiet: bool = False,
    metrics_collector: Optional["MetricsRecorder"] = None,
) -> RowResult:
    """
    Process a single row using domain models: find PDFs and Excel files, convert Excel to PDF, and merge them.

    Args:
        row: Row instance to process
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        quiet: If True, suppress row-level logger output (use when progress callback handles logging order)
        metrics_collector: Optional metrics recorder; when None, uses global get_metrics_collector() (for tests/mocks).

    Returns:
        RowResult with processing details
    """
    start_time = time.time()
    metrics = metrics_collector if metrics_collector is not None else get_metrics_collector()

    # 1. Validation: skip rows with no serial numbers
    if not row.has_serial_numbers():
        if not quiet:
            logger.warning(f"Row {row.row_index + 1}: No valid serial numbers, skipping...")
        metrics.record_counter("rows_skipped", tags={"reason": "no_serial_numbers"})
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            error_message="No valid serial numbers found"
        )

    if not quiet:
        logger.info(f"Row {row.row_index + 1}: Processing serial numbers: {', '.join(row.serial_numbers)}")

    # 2. Run pipeline (find, convert Excel, merge, cleanup)
    try:
        pipeline = run_row_pipeline(
            row.row_index,
            row.serial_numbers,
            source_folder,
            output_folder,
            fail_on_ambiguous=fail_on_ambiguous,
            quiet=quiet,
        )
    except ValueError:
        metrics.record_counter("ambiguous_matches")
        raise

    processing_time = time.time() - start_time
    metrics.record_timer("row_processing_time", processing_time)
    for _ in pipeline.source_files:
        metrics.record_counter("files_found")
    for _ in pipeline.missing:
        metrics.record_counter("files_missing")

    # 3. Map pipeline result to RowResult and record success/failure metrics
    row_result = _pipeline_result_to_row_result(row.row_index, pipeline, processing_time)
    if row_result.is_success() or row_result.status == RowStatus.PARTIAL:
        metrics.record_counter("rows_successful")
        try:
            if row_result.output_file:
                file_size_mb = row_result.output_file.stat().st_size / BYTES_PER_MB
                metrics.record_gauge("output_file_size_mb", file_size_mb)
        except Exception:
            pass
    elif row_result.is_failed():
        metrics.record_counter("rows_failed", tags={"reason": "merge_failed"})
    return row_result


def _progress_message_for_row_result(row_num: int, total_rows: int, row_result: RowResult) -> List[str]:
    """Return progress message line(s) for a row result (status line plus optional detail)."""
    pdf_count = sum(1 for p in row_result.files_found if p.suffix.lower() == ".pdf")
    excel_count = sum(1 for p in row_result.files_found if p.suffix.lower() in EXCEL_FILE_EXTENSIONS)
    if row_result.is_skipped():
        msg = f"Row {row_num} → No valid files found → Skipped" if row_result.files_missing else f"Row {row_num} → Skipped"
    elif row_result.is_success() or row_result.status == RowStatus.PARTIAL:
        msg = f"Row {row_num} → Found {pdf_count} PDFs, {excel_count} Excel → Success"
    else:
        msg = f"Row {row_num} → Found {pdf_count} PDFs, {excel_count} Excel → Failed"
    lines = [msg]
    missing = row_result.files_missing or []
    if missing:
        detail = f"  • {len(missing)} files not found ({', '.join(missing)})" if len(missing) <= MAX_MISSING_TO_LIST else f"  • {len(missing)} files not found"
        lines.append(detail)
    elif row_result.is_skipped() and not row_result.files_found:
        lines.append("  • No valid files to merge")
    return lines


def process_job(
    job: MergeJob,
    fail_on_ambiguous: bool = True,
    on_progress: Optional[ProgressCallback] = None,
    metrics_collector: Optional["MetricsRecorder"] = None,
) -> MergeResult:
    """
    Process a merge job using domain models.

    Args:
        job: MergeJob instance to process
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        on_progress: Optional callback (step, current, total, message) for progress updates
        metrics_collector: Optional metrics recorder; when None, uses global get_metrics_collector() (for tests/mocks).

    Returns:
        MergeResult with detailed processing results
    """
    job.output_folder.mkdir(parents=True, exist_ok=True)

    total_rows = job.get_total_rows()
    result = MergeResult(
        total_rows=total_rows,
        successful_merges=0,
        job_id=job.job_id,
    )

    if total_rows == 0:
        logger.info("Job has no rows to process; returning empty result")
        result.total_processing_time = 0.0
        return result

    start_time = time.time()
    metrics = metrics_collector if metrics_collector is not None else get_metrics_collector()
    metrics.record_counter("jobs_started")

    try:
        use_progress = on_progress is not None
        for idx, row in enumerate(job.rows):
            row_num = row.row_index + 1

            # Single row start message (avoids duplicate with process_row_with_models log)
            if on_progress:
                serials = ", ".join(row.serial_numbers) if row.serial_numbers else "no serial numbers"
                on_progress(PROGRESS_PROCESSING, row_num, total_rows, f"Processing Row {row_num}... ({serials})")

            row_result = process_row_with_models(
                row,
                job.source_folder,
                job.output_folder,
                fail_on_ambiguous=fail_on_ambiguous,
                quiet=use_progress,
                metrics_collector=metrics,
            )
            result.add_row_result(row_result)

            if on_progress:
                msg = _progress_message_for_row_result(row_num, total_rows, row_result)
                for line in msg:
                    on_progress(PROGRESS_PROCESSING, row_num, total_rows, line)
        
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
        result.add_row_result(RowResult.failed(row_index=row.row_index, error_message=str(e)))
        return result
    except ValueError as e:
        logger.error(f"Ambiguous match error: {e}")
        metrics.record_counter("jobs_failed", tags={"error_type": "AmbiguousMatch"})
        result.total_processing_time = time.time() - start_time
        result.add_row_result(RowResult.failed(row_index=row.row_index, error_message=str(e)))
        return result
    except Exception as e:
        logger.error(f"Unexpected error processing job: {e}")
        metrics.record_counter("jobs_failed", tags={"error_type": "UnexpectedError"})
        result.total_processing_time = time.time() - start_time
        result.add_row_result(RowResult.failed(row_index=row.row_index, error_message=str(e)))
        return result


def process_file(
    file_path: Path,
    source_folder: Path,
    output_folder: Path,
    required_column: str = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN,
    on_progress: Optional[ProgressCallback] = None,
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
        on_progress: Optional callback (step, current, total, message) for progress updates

    Returns:
        ProcessingResult with statistics about the processing
    """
    if on_progress:
        on_progress(PROGRESS_LOADING, 0, 0, "Reading input file...")

    # Use domain models internally but return legacy result
    job = MergeJob.create(
        input_file=file_path,
        source_folder=source_folder,
        output_folder=output_folder,
        required_column=required_column,
    )

    # Load rows from file
    try:
        for row_index, row_data in enumerate(read_data_file(file_path), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return ProcessingResult(total_rows=0, successful_merges=0, failed_rows=[])

    total_rows = job.get_total_rows()
    if on_progress:
        on_progress(PROGRESS_LOADING, total_rows, total_rows, f"Loaded {total_rows} rows")

    # Process job
    merge_result = process_job(job, on_progress=on_progress)
    # Legacy API: callers expect ProcessingResult
    return ProcessingResult(
        total_rows=merge_result.total_rows,
        successful_merges=merge_result.successful_merges,
        failed_rows=merge_result.failed_rows
    )
