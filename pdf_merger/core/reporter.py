"""
Reporter module.
Format processing results for UI display.
"""

from ..processor import ProcessingResult
from ..logger import get_logger

logger = get_logger("core.reporter")


def format_result_summary(result: ProcessingResult) -> str:
    """
    Format a brief summary of the processing result.
    
    Args:
        result: ProcessingResult object
        
    Returns:
        Formatted summary string
    """
    lines = [
        "=" * 60,
        "Processing Complete",
        "=" * 60,
        f"Total rows processed: {result.total_rows}",
        f"Successfully merged PDFs: {result.successful_merges}",
        f"Failed rows: {len(result.failed_rows)}",
    ]
    
    if result.failed_rows:
        failed_str = ', '.join(map(str, result.failed_rows))
        if len(failed_str) > 100:
            failed_str = failed_str[:97] + "..."
        lines.append(f"Failed row numbers: {failed_str}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_result_detailed(result: ProcessingResult) -> str:
    """
    Format a detailed report of the processing result.
    
    Args:
        result: ProcessingResult object
        
    Returns:
        Formatted detailed report string
    """
    lines = [
        "=" * 60,
        "Detailed Processing Report",
        "=" * 60,
        "",
        f"Total rows in input file: {result.total_rows}",
        f"Successfully merged PDFs: {result.successful_merges}",
        f"Failed or skipped rows: {len(result.failed_rows)}",
        "",
    ]
    
    if result.failed_rows:
        lines.append("Failed/Skipped Row Numbers:")
        for row_num in result.failed_rows:
            lines.append(f"  - Row {row_num}")
        lines.append("")
    
    success_rate = (result.successful_merges / result.total_rows * 100) if result.total_rows > 0 else 0
    lines.append(f"Success rate: {success_rate:.1f}%")
    lines.append("=" * 60)
    
    return "\n".join(lines)
