"""
Reporter module.
Format processing results for UI display.
Supports both legacy ProcessingResult and new MergeResult domain models.
"""

from typing import Union
from ..processor import ProcessingResult
from ..models import MergeResult, RowStatus
from ..constants import Constants
from ..logger import get_logger

logger = get_logger("core.reporter")

# Module-level constants
MAX_DISPLAY_STRING_LENGTH = Constants.MAX_DISPLAY_STRING_LENGTH
PERCENTAGE_MULTIPLIER = Constants.PERCENTAGE_MULTIPLIER


def format_result_summary(result: Union[ProcessingResult, MergeResult]) -> str:
    """
    Format a brief summary of the processing result.
    
    Args:
        result: ProcessingResult or MergeResult object
        
    Returns:
        Formatted summary string
    """
    # Handle both legacy and new result types
    total_rows = result.total_rows
    successful = result.successful_merges
    failed = len(result.failed_rows)
    skipped = len(result.skipped_rows) if isinstance(result, MergeResult) else 0
    
    lines = [
        "=" * 60,
        "Processing Complete",
        "=" * 60,
        f"Total rows processed: {total_rows}",
        f"Successfully merged PDFs: {successful}",
        f"Failed rows: {failed}",
    ]
    
    if skipped > 0:
        lines.append(f"Skipped rows: {skipped}")
    
    if result.failed_rows:
        failed_str = ', '.join(map(str, result.failed_rows))
        if len(failed_str) > MAX_DISPLAY_STRING_LENGTH:
            failed_str = failed_str[:MAX_DISPLAY_STRING_LENGTH - 3] + "..."
        lines.append(f"Failed row numbers: {failed_str}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_result_detailed(result: Union[ProcessingResult, MergeResult]) -> str:
    """
    Format a detailed report of the processing result.
    
    Args:
        result: ProcessingResult or MergeResult object
        
    Returns:
        Formatted detailed report string
    """
    # Handle both legacy and new result types
    total_rows = result.total_rows
    successful = result.successful_merges
    failed = len(result.failed_rows)
    skipped = len(result.skipped_rows) if isinstance(result, MergeResult) else 0
    success_rate = result.get_success_rate() if isinstance(result, MergeResult) else (
        (successful / total_rows * PERCENTAGE_MULTIPLIER) if total_rows > 0 else 0
    )
    
    lines = [
        "=" * 60,
        "Detailed Processing Report",
        "=" * 60,
        "",
        f"Total rows in input file: {total_rows}",
        f"Successfully merged PDFs: {successful}",
        f"Failed rows: {failed}",
    ]
    
    if skipped > 0:
        lines.append(f"Skipped rows: {skipped}")
    lines.append("")
    
    if result.failed_rows:
        lines.append("Failed Row Numbers:" if isinstance(result, MergeResult) else "Failed/Skipped Row Numbers:")
        for row_num in result.failed_rows:
            lines.append(f"  - Row {row_num}")
        lines.append("")
    
    if isinstance(result, MergeResult):
        if result.skipped_rows:
            lines.append("Skipped Row Numbers:")
            for row_num in result.skipped_rows:
                lines.append(f"  - Row {row_num}")
            lines.append("")
        
        # Add detailed row results if available
        if result.row_results:
            lines.append("Row Details:")
            for row_result in result.row_results:
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
        
        if result.total_processing_time:
            lines.append(f"Total processing time: {result.total_processing_time:.2f} seconds")
            lines.append("")
    
    lines.append(f"Success rate: {success_rate:.1f}%")
    lines.append("=" * 60)
    
    return "\n".join(lines)
