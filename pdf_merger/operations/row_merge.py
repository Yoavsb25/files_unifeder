"""
Per-row merge facade.
Single entry point for core to perform find-source, convert-excel, and merge-pdf I/O.
Core depends only on this facade and the MergeOperations protocol, not on concrete modules.
"""

import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import Row, RowResult, RowStatus
from ..core.constants import Constants
from ..utils.logging_utils import get_logger

from .protocols import MergeOperations
from .pdf_merger import find_source_file, merge_pdfs
from .excel_to_pdf_converter import convert_excel_to_pdf

logger = get_logger("operations.row_merge")

EXCEL_FILE_EXTENSIONS = Constants.EXCEL_FILE_EXTENSIONS
OUTPUT_FILENAME_PATTERN = Constants.OUTPUT_FILENAME_PATTERN


def _default_merge_operations() -> MergeOperations:
    """Default implementation that uses real pdf_merger and excel converter."""
    return _DefaultMergeOperations()


class _DefaultMergeOperations:
    """Default MergeOperations implementation using pdf_merger and excel_to_pdf_converter."""

    def find_source_file(
        self,
        folder: Path,
        filename: str,
        fail_on_ambiguous: bool = False,
    ) -> Optional[Path]:
        return find_source_file(folder, filename, fail_on_ambiguous=fail_on_ambiguous)

    def merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> bool:
        return merge_pdfs(pdf_paths, output_path)


def _convert_excel_files_to_pdfs(
    source_files: List[Path],
    output_folder: Path,
) -> Tuple[List[Path], List[Path]]:
    """Convert Excel files to PDFs; return (pdf_paths, temp_pdf_files) for cleanup."""
    pdf_paths: List[Path] = []
    temp_pdf_files: List[Path] = []

    for source_path in source_files:
        if source_path.suffix.lower() in EXCEL_FILE_EXTENSIONS:
            logger.info(f"  Converting {source_path.name} to PDF...")
            temp_pdf = tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False,
                dir=output_folder.parent if output_folder.parent.exists() else None,
            )
            temp_pdf.close()
            temp_pdf_path = Path(temp_pdf.name)
            temp_pdf_files.append(temp_pdf_path)

            if convert_excel_to_pdf(source_path, temp_pdf_path):
                pdf_paths.append(temp_pdf_path)
                logger.info(f"  ✓ Converted {source_path.name} to PDF")
            else:
                logger.error(f"  ✗ Failed to convert {source_path.name} to PDF")
        else:
            pdf_paths.append(source_path)

    return pdf_paths, temp_pdf_files


def _cleanup_temp_files(temp_pdf_files: List[Path]) -> None:
    """Remove temporary PDF files."""
    for temp_pdf in temp_pdf_files:
        try:
            if temp_pdf.exists():
                temp_pdf.unlink()
                logger.debug(f"  Cleaned up temporary file: {temp_pdf.name}")
        except Exception as e:
            logger.warning(f"  Failed to clean up temporary file {temp_pdf.name}: {e}")


def run_merge_for_row(
    row: Row,
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = True,
    operations: Optional[MergeOperations] = None,
) -> RowResult:
    """
    Find source files, convert Excel to PDF as needed, and merge PDFs for one row.
    Single facade for all per-row I/O so core does not depend on concrete operation modules.

    Args:
        row: Row with serial numbers to resolve
        source_folder: Folder containing PDF and Excel files
        output_folder: Folder for merged output PDF
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches
        operations: Optional MergeOperations implementation (default: real filesystem)

    Returns:
        RowResult with status, paths, and optional error message

    Raises:
        ValueError: When fail_on_ambiguous is True and an ambiguous match is found
    """
    ops = operations if operations is not None else _default_merge_operations()
    start_time = time.time()

    if not row.has_serial_numbers():
        logger.warning(f"Row {row.row_index + 1}: No valid serial numbers, skipping...")
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            error_message="No valid serial numbers found",
        )

    logger.info(f"Row {row.row_index + 1}: Processing serial numbers: {', '.join(row.serial_numbers)}")

    source_files: List[Path] = []
    missing_serial_numbers: List[str] = []

    for serial_number in row.serial_numbers:
        try:
            source_path = ops.find_source_file(
                source_folder, serial_number, fail_on_ambiguous=fail_on_ambiguous
            )
            if source_path:
                source_files.append(source_path)
                logger.info(f"  Found: {source_path.name}")
            else:
                missing_serial_numbers.append(serial_number)
                logger.warning(f"  File not found for serial number '{serial_number}'")
        except ValueError:
            if fail_on_ambiguous:
                raise

    if not source_files:
        logger.warning(f"Row {row.row_index + 1}: No files found for any serial numbers, skipping...")
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            files_missing=missing_serial_numbers,
            error_message="No source files found",
        )

    temp_pdf_files: List[Path] = []
    try:
        pdf_paths, temp_pdf_files = _convert_excel_files_to_pdfs(source_files, output_folder)

        if not pdf_paths:
            logger.warning(
                f"Row {row.row_index + 1}: No PDF files to merge (conversions may have failed), skipping..."
            )
            return RowResult(
                row_index=row.row_index,
                status=RowStatus.FAILED,
                files_found=source_files,
                files_missing=missing_serial_numbers,
                error_message="No PDF files available for merging",
            )

        output_filename = OUTPUT_FILENAME_PATTERN.format(row.row_index + 1)
        output_path = output_folder / output_filename

        logger.info(f"  Merging {len(pdf_paths)} file(s) into {output_filename}...")
        success = ops.merge_pdfs(pdf_paths, output_path)

        processing_time = time.time() - start_time

        if success:
            logger.info(f"  ✓ Successfully created {output_filename}")
            status = RowStatus.PARTIAL if missing_serial_numbers else RowStatus.SUCCESS
            return RowResult(
                row_index=row.row_index,
                status=status,
                output_file=output_path,
                files_found=source_files,
                files_missing=missing_serial_numbers,
                processing_time=processing_time,
            )
        else:
            logger.error(f"  ✗ Failed to create {output_filename}")
            return RowResult(
                row_index=row.row_index,
                status=RowStatus.FAILED,
                files_found=source_files,
                files_missing=missing_serial_numbers,
                error_message="Failed to merge PDFs",
                processing_time=processing_time,
            )
    finally:
        _cleanup_temp_files(temp_pdf_files)
