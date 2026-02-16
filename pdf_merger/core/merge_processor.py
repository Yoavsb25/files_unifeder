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
from typing import TYPE_CHECKING, List, Optional

from ..models import MergeJob, MergeResult, Row, RowResult, RowStatus
from ..observability import get_metrics_collector
from ..utils.exceptions import PDFMergerError
from ..utils.logging_utils import get_logger
from .constants import Constants
from .row_pipeline import RowPipelineResult, run_row_pipeline
from .types import PROGRESS_PROCESSING, ProgressCallback

if TYPE_CHECKING:
    from ..observability import MetricsRecorder

logger = get_logger("pdf_merger.core.merge_processor")

# Module-level aliases for readability in hot paths (see docs ARCHITECTURE Conventions).
EXCEL_FILE_EXTENSIONS = Constants.EXCEL_FILE_EXTENSIONS
BYTES_PER_MB = Constants.BYTES_PER_MB
MAX_MISSING_TO_LIST = Constants.MAX_MISSING_TO_LIST


def _pipeline_result_to_row_result(
    row_index: int,
    pipeline: RowPipelineResult,
    processing_time: float,
) -> RowResult:
    """Map RowPipelineResult to RowResult. Maps pipeline error_message to RowStatus and RowResult fields."""
    if not pipeline.source_files:
        return RowResult(
            row_index=row_index,
            status=RowStatus.SKIPPED,
            files_missing=pipeline.missing,
            error_message=pipeline.error_message or Constants.NO_SOURCE_FILES,
        )
    if pipeline.error_message == Constants.NO_PDF_AVAILABLE:
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
        error_message=pipeline.error_message or Constants.MERGE_FAILED,
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
    Process a single row using domain models: find source files, merge only PDFs, and skip Excel files.

    Args:
        row: Row instance to process
        source_folder: Folder containing source files
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
            error_message="No valid serial numbers found",
        )

    if not quiet:
        logger.info(
            f"Row {row.row_index + 1}: Processing serial numbers: {', '.join(row.serial_numbers)}"
        )

    # 2. Run pipeline (find, keep PDFs, merge, cleanup)
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
        except OSError:
            pass
    elif row_result.is_failed():
        metrics.record_counter("rows_failed", tags={"reason": "merge_failed"})
    return row_result


def _progress_message_for_row_result(
    row_num: int, total_rows: int, row_result: RowResult
) -> List[str]:
    """Return progress message line(s) for a row result (status line plus optional detail)."""
    pdf_count = sum(1 for p in row_result.files_found if p.suffix.lower() == ".pdf")
    excel_count = sum(
        1 for p in row_result.files_found if p.suffix.lower() in EXCEL_FILE_EXTENSIONS
    )
    if row_result.is_skipped():
        msg = (
            f"Row {row_num} → No valid files found → Skipped"
            if row_result.files_missing
            else f"Row {row_num} → Skipped"
        )
    elif row_result.is_success() or row_result.status == RowStatus.PARTIAL:
        msg = f"Row {row_num} → Found {pdf_count} PDFs, {excel_count} Excel → Success"
    else:
        msg = f"Row {row_num} → Found {pdf_count} PDFs, {excel_count} Excel → Failed"
    lines = [msg]
    if excel_count:
        skipped_excel_names = [
            p.name for p in row_result.files_found if p.suffix.lower() in EXCEL_FILE_EXTENSIONS
        ]
        if len(skipped_excel_names) <= MAX_MISSING_TO_LIST:
            lines.append(
                f"  • This is an Excel file; skipping (only PDFs are processed): {', '.join(skipped_excel_names)}"
            )
        else:
            lines.append(
                f"  • This is an Excel file; skipping (only PDFs are processed): {len(skipped_excel_names)} file(s)"
            )
    missing = row_result.files_missing or []
    if missing:
        detail = (
            f"  • {len(missing)} files not found ({', '.join(missing)})"
            if len(missing) <= MAX_MISSING_TO_LIST
            else f"  • {len(missing)} files not found"
        )
        lines.append(detail)
    elif row_result.is_skipped() and not row_result.files_found:
        lines.append("  • No valid files to merge")
    return lines


def _record_job_failure(
    result: MergeResult,
    row_index: int,
    start_time: float,
    exception: Exception,
    error_type: str,
    metrics: "MetricsRecorder",
) -> None:
    """Record a job-level failure: set timing, log, record metric, and add a failed RowResult."""
    result.total_processing_time = time.time() - start_time
    logger.error(f"{error_type}: {exception}")
    metrics.record_counter("jobs_failed", tags={"error_type": error_type})
    result.add_row_result(RowResult.failed(row_index=row_index, error_message=str(exception)))


def _process_single_row_and_report(
    row: Row,
    source_folder: Path,
    output_folder: Path,
    total_rows: int,
    fail_on_ambiguous: bool,
    on_progress: Optional[ProgressCallback],
    metrics: "MetricsRecorder",
) -> RowResult:
    """Process one row, optionally report progress via callback; returns RowResult for caller to add to MergeResult."""
    row_num = row.row_index + 1
    if on_progress:
        serials = ", ".join(row.serial_numbers) if row.serial_numbers else "no serial numbers"
        on_progress(
            PROGRESS_PROCESSING, row_num, total_rows, f"Processing Row {row_num}... ({serials})"
        )

    row_result = process_row_with_models(
        row,
        source_folder,
        output_folder,
        fail_on_ambiguous=fail_on_ambiguous,
        quiet=on_progress is not None,
        metrics_collector=metrics,
    )

    if on_progress:
        for line in _progress_message_for_row_result(row_num, total_rows, row_result):
            on_progress(PROGRESS_PROCESSING, row_num, total_rows, line)

    return row_result


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
    current_row_index = 0

    try:
        for row in job.rows:
            current_row_index = row.row_index
            row_result = _process_single_row_and_report(
                row,
                job.source_folder,
                job.output_folder,
                total_rows,
                fail_on_ambiguous,
                on_progress,
                metrics,
            )
            result.add_row_result(row_result)

        result.total_processing_time = time.time() - start_time
        metrics.record_timer("job_processing_time", result.total_processing_time)
        metrics.record_counter("jobs_completed")
        metrics.record_gauge("job_success_rate", result.get_success_rate())

        logger.info(f"Job {job.job_id or 'default'} completed: {result}")
        return result

    except PDFMergerError as e:
        _record_job_failure(result, current_row_index, start_time, e, "PDFMergerError", metrics)
        return result
    except ValueError as e:
        _record_job_failure(result, current_row_index, start_time, e, "AmbiguousMatch", metrics)
        return result
    # Intentional: see ARCHITECTURE.md "Intentional broad catches". Reason: job must always return MergeResult.
    except Exception as e:
        _record_job_failure(result, current_row_index, start_time, e, "UnexpectedError", metrics)
        return result
