"""
Result reporter module.
Single place for MergeResult → display strings (summary and detailed).
UI and handlers must not duplicate this logic; use format_result_summary,
format_result_detailed, and format_failed_rows_display from here (or via core).
Uses ResultView built from MergeResult.
"""

from typing import List

from ..models import MergeResult, RowStatus
from ..utils.logging_utils import get_logger
from .constants import Constants
from .result_view import as_result_view

logger = get_logger("pdf_merger.core.result_reporter")

# Module-level constants
MAX_DISPLAY_STRING_LENGTH = Constants.MAX_DISPLAY_STRING_LENGTH
_SEPARATOR = "=" * 60


def format_failed_rows_display(
    failed_rows: List[int],
    max_length: int = Constants.MAX_DISPLAY_STRING_LENGTH,
) -> str:
    """
    Format failed row indices as a truncated string for display (e.g. "1, 2, 5" or "1, 2, 5, ...").

    Args:
        failed_rows: List of failed row indices (0-based; displayed as 1-based for users).
        max_length: Maximum string length before truncation with "...".

    Returns:
        Comma-separated string of 1-based row numbers, truncated if over max_length.
    """
    # Display 1-based row numbers to match "Processing Row 1...", "Row 1 → Failed", etc.
    failed_str = ", ".join(str(i + 1) for i in failed_rows)
    if len(failed_str) > max_length:
        failed_str = failed_str[: max_length - 3] + "..."
    return failed_str


def format_result_summary(result: MergeResult) -> str:
    """
    Format a brief summary of the processing result.

    Args:
        result: MergeResult object

    Returns:
        Formatted summary string
    """
    view = as_result_view(result)
    lines = [
        _SEPARATOR,
        "Processing Complete",
        _SEPARATOR,
        f"Total rows processed: {view.total_rows}",
        f"Successfully merged PDFs: {view.successful_merges}",
        f"Failed rows: {len(view.failed_rows)}",
    ]
    if view.skipped_rows:
        lines.append(f"Skipped rows: {len(view.skipped_rows)}")
    if view.failed_rows:
        lines.append(f"Failed row numbers: {format_failed_rows_display(view.failed_rows)}")
    lines.append(_SEPARATOR)
    return "\n".join(lines)


def format_result_detailed(result: MergeResult) -> str:
    """
    Format a detailed report of the processing result.

    Args:
        result: MergeResult object

    Returns:
        Formatted detailed report string
    """
    view = as_result_view(result)
    lines = [
        _SEPARATOR,
        "Detailed Processing Report",
        _SEPARATOR,
        "",
        f"Total rows in input file: {view.total_rows}",
        f"Successfully merged PDFs: {view.successful_merges}",
        f"Failed rows: {len(view.failed_rows)}",
    ]
    if view.skipped_rows:
        lines.append(f"Skipped rows: {len(view.skipped_rows)}")
    lines.append("")
    if view.failed_rows:
        lines.append("Failed Row Numbers:" if view.row_results else "Failed/Skipped Row Numbers:")
        for row_index in view.failed_rows:
            lines.append(f"  - Row {row_index + 1}")
        lines.append("")
    if view.skipped_rows:
        lines.append("Skipped Row Numbers:")
        for row_index in view.skipped_rows:
            lines.append(f"  - Row {row_index + 1}")
        lines.append("")
    if view.row_results:
        lines.append("Row Details:")
        for row_result in view.row_results:
            if row_result.is_failed():
                lines.append(
                    f"  Row {row_result.row_index + 1}: FAILED - {row_result.error_message or 'Unknown error'}"
                )
                if row_result.files_missing:
                    lines.append(f"    Missing files: {', '.join(row_result.files_missing)}")
            elif row_result.is_skipped():
                lines.append(
                    f"  Row {row_result.row_index + 1}: SKIPPED - {row_result.error_message or 'No serial numbers'}"
                )
            elif row_result.status == RowStatus.PARTIAL:
                lines.append(f"  Row {row_result.row_index + 1}: PARTIAL - Some files missing")
                if row_result.files_missing:
                    lines.append(f"    Missing files: {', '.join(row_result.files_missing)}")
        lines.append("")
    if view.total_processing_time:
        lines.append(f"Total processing time: {view.total_processing_time:.2f} seconds")
        lines.append("")
    lines.append(f"Success rate: {view.success_rate:.1f}%")
    lines.append(_SEPARATOR)
    return "\n".join(lines)
