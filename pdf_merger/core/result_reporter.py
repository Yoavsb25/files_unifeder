"""
Result reporter module.
Format processing results for UI display.
Supports both legacy ProcessingResult and new MergeResult via ResultView abstraction.
"""

from typing import Union
from .result_types import ProcessingResult
from ..models import MergeResult, RowStatus
from .constants import Constants
from .result_view import ResultView, as_result_view
from ..utils.logging_utils import get_logger

logger = get_logger("pdf_merger.core.result_reporter")

# Module-level constants
MAX_DISPLAY_STRING_LENGTH = Constants.MAX_DISPLAY_STRING_LENGTH
_SEPARATOR = "=" * 60


def format_result_summary(result: Union[ProcessingResult, MergeResult]) -> str:
    """
    Format a brief summary of the processing result.
    
    Args:
        result: ProcessingResult or MergeResult object
        
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
        failed_str = ", ".join(map(str, view.failed_rows))
        if len(failed_str) > MAX_DISPLAY_STRING_LENGTH:
            failed_str = failed_str[: MAX_DISPLAY_STRING_LENGTH - 3] + "..."
        lines.append(f"Failed row numbers: {failed_str}")
    lines.append(_SEPARATOR)
    return "\n".join(lines)


def format_result_detailed(result: Union[ProcessingResult, MergeResult]) -> str:
    """
    Format a detailed report of the processing result.
    
    Args:
        result: ProcessingResult or MergeResult object
        
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
        for row_num in view.failed_rows:
            lines.append(f"  - Row {row_num}")
        lines.append("")
    if view.skipped_rows:
        lines.append("Skipped Row Numbers:")
        for row_num in view.skipped_rows:
            lines.append(f"  - Row {row_num}")
        lines.append("")
    if view.row_results:
        lines.append("Row Details:")
        for row_result in view.row_results:
            if row_result.is_failed():
                lines.append(f"  Row {row_result.row_index + 1}: FAILED - {row_result.error_message or 'Unknown error'}")
                if row_result.files_missing:
                    lines.append(f"    Missing files: {', '.join(row_result.files_missing)}")
            elif row_result.is_skipped():
                lines.append(f"  Row {row_result.row_index + 1}: SKIPPED - {row_result.error_message or 'No serial numbers'}")
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
