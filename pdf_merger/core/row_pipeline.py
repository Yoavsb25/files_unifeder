"""
Row pipeline: find source files, convert Excel to PDF, merge, cleanup.
Single responsibility for one-row processing; merge_processor orchestrates rows and maps to RowResult.
"""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from ..operations.pdf_merger import find_source_file, merge_pdfs
from ..operations.excel_to_pdf_converter import convert_excel_to_pdf
from ..utils.logging_utils import get_logger
from .constants import Constants

logger = get_logger("pdf_merger.core.row_pipeline")

# Module-level aliases for readability in hot paths (see docs ARCHITECTURE Conventions).
EXCEL_FILE_EXTENSIONS = Constants.EXCEL_FILE_EXTENSIONS
OUTPUT_FILENAME_PATTERN = Constants.OUTPUT_FILENAME_PATTERN


@dataclass
class RowPipelineResult:
    """Result of the find/convert/merge pipeline for one row."""
    success: bool
    output_path: Optional[Path] = None
    source_files: List[Path] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


def _convert_excel_files_to_pdfs(
    source_files: List[Path], output_folder: Path, quiet: bool = False
) -> Tuple[List[Path], List[Path]]:
    """Convert Excel files to PDFs; return (pdf_paths, temp_pdf_files) for cleanup."""
    pdf_paths = []
    temp_pdf_files = []

    for source_path in source_files:
        if source_path.suffix.lower() in EXCEL_FILE_EXTENSIONS:
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
            pdf_paths.append(source_path)

    return pdf_paths, temp_pdf_files


def _cleanup_temp_files(temp_pdf_files: List[Path], quiet: bool = False) -> None:
    """Clean up temporary PDF files."""
    for temp_pdf in temp_pdf_files:
        try:
            if temp_pdf.exists():
                temp_pdf.unlink()
                if not quiet:
                    logger.debug(f"  Cleaned up temporary file: {temp_pdf.name}")
        except Exception as e:
            if not quiet:
                logger.warning(f"  Failed to clean up temporary file {temp_pdf.name}: {e}")


def run_row_pipeline(
    row_index: int,
    serial_numbers: List[str],
    source_folder: Path,
    output_folder: Path,
    fail_on_ambiguous: bool = False,
    quiet: bool = False,
) -> RowPipelineResult:
    """
    Find source files, convert Excel to PDF, merge, cleanup for one row.
    Caller is responsible for parsing/validation and mapping to RowResult or legacy bool.
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
        return RowPipelineResult(
            success=False,
            source_files=[],
            missing=missing,
            error_message=Constants.NO_SOURCE_FILES,
        )
    temp_pdf_files: List[Path] = []
    try:
        pdf_paths, temp_pdf_files = _convert_excel_files_to_pdfs(source_files, output_folder, quiet=quiet)
        if not pdf_paths:
            return RowPipelineResult(
                success=False,
                source_files=source_files,
                missing=missing,
                error_message=Constants.NO_PDF_AVAILABLE,
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
        return RowPipelineResult(
            success=success,
            output_path=output_path if success else None,
            source_files=source_files,
            missing=missing,
            error_message=None if success else Constants.MERGE_FAILED,
        )
    finally:
        _cleanup_temp_files(temp_pdf_files, quiet=quiet)
