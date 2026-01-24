"""
Reporter module.
Format processing results for UI display.
Supports both legacy ProcessingResult and new MergeResult domain models.
"""

from typing import Union
from ..processor import ProcessingResult
from ..models import MergeResult
from ..logger import get_logger

logger = get_logger("core.reporter")


def format_result_summary(result: Union[ProcessingResult, MergeResult]) -> str:
    """
    Format a brief summary of the processing result.
    
    Args:
        result: ProcessingResult or MergeResult object
        
    Returns:
        Formatted summary string
    """
    # Handle both legacy and new result types
    if isinstance(result, MergeResult):
        total_rows = result.total_rows
        successful = result.successful_merges
        failed = len(result.failed_rows)
        skipped = len(result.skipped_rows)
    else:
        total_rows = result.total_rows
        successful = result.successful_merges
        failed = len(result.failed_rows)
        skipped = 0
    
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
    
    if isinstance(result, MergeResult) and result.failed_rows:
        failed_str = ', '.join(map(str, result.failed_rows))
        if len(failed_str) > 100:
            failed_str = failed_str[:97] + "..."
        lines.append(f"Failed row numbers: {failed_str}")
    elif hasattr(result, 'failed_rows') and result.failed_rows:
        failed_str = ', '.join(map(str, result.failed_rows))
        if len(failed_str) > 100:
            failed_str = failed_str[:97] + "..."
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
    if isinstance(result, MergeResult):
        total_rows = result.total_rows
        successful = result.successful_merges
        failed = len(result.failed_rows)
        skipped = len(result.skipped_rows)
        success_rate = result.get_success_rate()
        
        lines = [
            "=" * 60,
            "Detailed Processing Report",
            "=" * 60,
            "",
            f"Total rows in input file: {total_rows}",
            f"Successfully merged PDFs: {successful}",
            f"Failed rows: {failed}",
            f"Skipped rows: {skipped}",
            "",
        ]
        
        if result.failed_rows:
            lines.append("Failed Row Numbers:")
            for row_num in result.failed_rows:
                lines.append(f"  - Row {row_num}")
            lines.append("")
        
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
                elif row_result.status.value == 'partial':
                    lines.append(f"  Row {row_result.row_index + 1}: PARTIAL - Some files missing")
                    if row_result.files_missing:
                        lines.append(f"    Missing files: {', '.join(row_result.files_missing)}")
            lines.append("")
        
        if result.total_processing_time:
            lines.append(f"Total processing time: {result.total_processing_time:.2f} seconds")
            lines.append("")
    else:
        # Legacy ProcessingResult
        total_rows = result.total_rows
        successful = result.successful_merges
        failed = len(result.failed_rows)
        success_rate = (successful / total_rows * 100) if total_rows > 0 else 0
        
        lines = [
            "=" * 60,
            "Detailed Processing Report",
            "=" * 60,
            "",
            f"Total rows in input file: {total_rows}",
            f"Successfully merged PDFs: {successful}",
            f"Failed or skipped rows: {failed}",
            "",
        ]
        
        if result.failed_rows:
            lines.append("Failed/Skipped Row Numbers:")
            for row_num in result.failed_rows:
                lines.append(f"  - Row {row_num}")
            lines.append("")
    
    lines.append(f"Success rate: {success_rate:.1f}%")
    lines.append("=" * 60)
    
    return "\n".join(lines)
