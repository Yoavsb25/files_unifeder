"""
Merge processor module.
Job execution and row-level logic (process_job, process_row_with_models).
Do not add UI-facing API or row loading from file here—those belong in
merge_orchestrator. When on_progress is provided, row-level logs are
suppressed (quiet=True) to avoid duplicate or out-of-order messages.
Log levels: user-visible milestones = info, per-row detail = debug.
"""

import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .types import ProgressCallback, PROGRESS_LOADING, PROGRESS_PROCESSING

from ..operations.pdf_merger import find_source_file, merge_pdfs
from ..operations.excel_to_pdf_converter import convert_excel_to_pdf
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
from ..matching import MatchBehavior

logger = get_logger("pdf_merger.core.merge_processor")

# Module-level constants
EXCEL_FILE_EXTENSIONS = Constants.EXCEL_FILE_EXTENSIONS
OUTPUT_FILENAME_PATTERN = Constants.OUTPUT_FILENAME_PATTERN
BYTES_PER_MB = Constants.BYTES_PER_MB
MAX_MISSING_TO_LIST = Constants.MAX_MISSING_TO_LIST


from .result_types import ProcessingResult


def _convert_excel_files_to_pdfs(
    source_files: List[Path], output_folder: Path, quiet: bool = False
) -> Tuple[List[Path], List[Path]]:
    """
    Convert Excel files to PDFs and return both PDF paths and temporary file paths.

    Args:
        source_files: List of source file paths (PDF and Excel)
        output_folder: Output folder for temporary PDFs
        quiet: If True, suppress logger output (used when progress callback handles logging)

    Returns:
        Tuple of (pdf_paths, temp_pdf_files) for cleanup
    """
    pdf_paths = []
    temp_pdf_files = []

    for source_path in source_files:
        if source_path.suffix.lower() in EXCEL_FILE_EXTENSIONS:
            # Convert Excel to PDF
            if not quiet:
                logger.info(f"  Converting {source_path.name} to PDF...")
            temp_pdf = tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False,
                dir=output_folder.parent if output_folder.parent.exists() else None
            )
            temp_pdf.close()
            temp_pdf_path = Path(temp_pdf.name)
            temp_pdf_files.append(temp_pdf_path)
            
            if convert_excel_to_pdf(source_path, temp_pdf_path):
                pdf_paths.append(temp_pdf_path)
                if not quiet:
                    logger.info(f"  ✓ Converted {source_path.name} to PDF")
            else:
                if not quiet:
                    logger.error(f"  ✗ Failed to convert {source_path.name} to PDF")
        else:
            # Already a PDF file
            pdf_paths.append(source_path)
    
    return pdf_paths, temp_pdf_files


def _cleanup_temp_files(temp_pdf_files: List[Path], quiet: bool = False) -> None:
    """
    Clean up temporary PDF files.

    Args:
        temp_pdf_files: List of temporary file paths to clean up
        quiet: If True, suppress logger output
    """
    for temp_pdf in temp_pdf_files:
        try:
            if temp_pdf.exists():
                temp_pdf.unlink()
                if not quiet:
                    logger.debug(f"  Cleaned up temporary file: {temp_pdf.name}")
        except Exception as e:
            if not quiet:
                logger.warning(f"  Failed to clean up temporary file {temp_pdf.name}: {e}")


@dataclass
class _RowPipelineResult:
    """Internal result of the shared find/convert/merge pipeline for one row."""
    success: bool
    output_path: Optional[Path] = None
    source_files: List[Path] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


def _run_row_pipeline(
    row_index: int,
    serial_numbers: List[str],
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = False,
    quiet: bool = False,
) -> _RowPipelineResult:
    """
    Shared pipeline: find source files, convert Excel to PDF, merge, cleanup.
    Caller is responsible for parsing/validation and for mapping to legacy bool or RowResult.
    May raise ValueError on ambiguous match when fail_on_ambiguous is True.
    """
    source_files: List[Path] = []
    missing: List[str] = []
    for serial_number in serial_numbers:
        source_path = find_source_file(source_folder, serial_number, fail_on_ambiguous=fail_on_ambiguous)
        if source_path:
            source_files.append(source_path)
            if not quiet:
                logger.info(f"  Found: {source_path.name}")
        else:
            missing.append(serial_number)
            if not quiet:
                logger.warning(f"  File not found for serial number '{serial_number}'")
    if not source_files:
        return _RowPipelineResult(
            success=False,
            source_files=[],
            missing=missing,
            error_message="No source files found",
        )
    # Caller is responsible for cleanup; we always run _cleanup_temp_files in finally to avoid disk leak
    temp_pdf_files: List[Path] = []
    try:
        pdf_paths, temp_pdf_files = _convert_excel_files_to_pdfs(source_files, output_folder, quiet=quiet)
        if not pdf_paths:
            return _RowPipelineResult(
                success=False,
                source_files=source_files,
                missing=missing,
                error_message="No PDF files available for merging",
            )
        output_filename = OUTPUT_FILENAME_PATTERN.format(row_index + 1)
        output_path = output_folder / output_filename
        if not quiet:
            logger.info(f"  Merging {len(pdf_paths)} file(s) into {output_filename}...")
        success = merge_pdfs(pdf_paths, output_path)
        if not quiet:
            if success:
                logger.info(f"  ✓ Successfully created {output_filename}")
            else:
                logger.error(f"  ✗ Failed to create {output_filename}")
        return _RowPipelineResult(
            success=success,
            output_path=output_path if success else None,
            source_files=source_files,
            missing=missing,
            error_message=None if success else "Failed to merge PDFs",
        )
    finally:
        # Always cleanup temp PDFs to avoid disk leak
        _cleanup_temp_files(temp_pdf_files, quiet=quiet)


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
    pipeline = _run_row_pipeline(
        row_index, normalized_serial_numbers, source_folder, output_folder, fail_on_ambiguous=False, quiet=False
    )
    if not pipeline.success and not pipeline.source_files:
        logger.warning(f"Row {row_index + 1}: No files found for any serial numbers, skipping...")
    elif not pipeline.success and pipeline.error_message == "No PDF files available for merging":
        logger.warning(f"Row {row_index + 1}: No PDF files to merge (conversions may have failed), skipping...")
    return pipeline.success


def process_row_with_models(
    row: Row,
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = True,
    quiet: bool = False,
) -> RowResult:
    """
    Process a single row using domain models: find PDFs and Excel files, convert Excel to PDF, and merge them.

    Args:
        row: Row instance to process
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        quiet: If True, suppress row-level logger output (use when progress callback handles logging order)

    Returns:
        RowResult with processing details
    """
    start_time = time.time()
    metrics = get_metrics_collector()

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
    try:
        pipeline = _run_row_pipeline(
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
    if not pipeline.source_files:
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            files_missing=pipeline.missing,
            error_message=pipeline.error_message or "No source files found",
        )
    if pipeline.error_message == "No PDF files available for merging":
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.FAILED,
            files_found=pipeline.source_files,
            files_missing=pipeline.missing,
            error_message=pipeline.error_message,
        )
    if pipeline.success:
        metrics.record_counter("rows_successful")
        try:
            if pipeline.output_path:
                file_size_mb = pipeline.output_path.stat().st_size / BYTES_PER_MB
                metrics.record_gauge("output_file_size_mb", file_size_mb)
        except Exception:
            pass
        status = RowStatus.PARTIAL if pipeline.missing else RowStatus.SUCCESS
        return RowResult(
            row_index=row.row_index,
            status=status,
            output_file=pipeline.output_path,
            files_found=pipeline.source_files,
            files_missing=pipeline.missing,
            processing_time=processing_time,
        )
    metrics.record_counter("rows_failed", tags={"reason": "merge_failed"})
    return RowResult(
        row_index=row.row_index,
        status=RowStatus.FAILED,
        files_found=pipeline.source_files,
        files_missing=pipeline.missing,
        error_message=pipeline.error_message or "Failed to merge PDFs",
        processing_time=processing_time,
    )


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
) -> MergeResult:
    """
    Process a merge job using domain models.

    Args:
        job: MergeJob instance to process
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: True)
        on_progress: Optional callback (step, current, total, message) for progress updates

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
    metrics = get_metrics_collector()
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
