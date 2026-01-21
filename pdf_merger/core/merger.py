"""
Merger module.
Wrapper around process_file for UI consumption.
"""

from pathlib import Path
from typing import Optional

from ..processor import process_file, ProcessingResult
from ..enums import DEFAULT_REQUIRED_COLUMN
from ..logger import get_logger

logger = get_logger("core.merger")


def run_merge(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = DEFAULT_REQUIRED_COLUMN
) -> ProcessingResult:
    """
    Run the merge operation.
    
    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        
    Returns:
        ProcessingResult with statistics
    """
    logger.info(f"Starting merge operation")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  PDF directory: {pdf_dir}")
    logger.info(f"  Output directory: {output_dir}")
    
    try:
        result = process_file(
            file_path=input_file,
            source_folder=pdf_dir,
            output_folder=output_dir,
            required_column=required_column
        )
        
        logger.info(f"Merge operation completed")
        logger.info(f"  Total rows: {result.total_rows}")
        logger.info(f"  Successful: {result.successful_merges}")
        logger.info(f"  Failed: {len(result.failed_rows)}")
        
        return result
    except Exception as e:
        logger.error(f"Error during merge operation: {e}")
        raise
