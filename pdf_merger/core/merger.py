"""
Merger module.
Wrapper around process_file and process_job for UI consumption.
"""

from pathlib import Path
from typing import Optional

from ..processor import process_file, process_job, ProcessingResult
from ..models import MergeJob, MergeResult
from ..file_reader import read_data_file
from ..enums import DEFAULT_SERIAL_NUMBERS_COLUMN
from ..logger import get_logger

logger = get_logger("core.merger")


def run_merge(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN
) -> ProcessingResult:
    """
    Run the merge operation (legacy interface).
    
    Note: This function is kept for backward compatibility.
    New code should use run_merge_job() with domain models.
    
    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        
    Returns:
        ProcessingResult with statistics
    """
    logger.info(f"Starting merge operation")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  Source directory: {pdf_dir}")
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


def run_merge_job(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN,
    job_id: Optional[str] = None
) -> MergeResult:
    """
    Run the merge operation using domain models.
    
    Args:
        input_file: Path to CSV or Excel file
        pdf_dir: Path to folder containing PDF and Excel files
        output_dir: Path to output folder
        required_column: Name of the column containing serial numbers
        job_id: Optional job identifier for tracking
        
    Returns:
        MergeResult with detailed processing results
    """
    logger.info(f"Starting merge job {job_id or 'default'}")
    logger.info(f"  Input file: {input_file}")
    logger.info(f"  Source directory: {pdf_dir}")
    logger.info(f"  Output directory: {output_dir}")
    
    # Create merge job
    job = MergeJob.create(
        input_file=input_file,
        source_folder=pdf_dir,
        output_folder=output_dir,
        required_column=required_column,
        job_id=job_id
    )
    
    # Load rows from file
    try:
        from ..models import Row
        for row_index, row_data in enumerate(read_data_file(input_file), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return MergeResult(
            total_rows=0,
            successful_merges=0,
            job_id=job_id
        )
    
    # Process job
    result = process_job(job)
    
    logger.info(f"Merge job {job_id or 'default'} completed")
    logger.info(f"  Total rows: {result.total_rows}")
    logger.info(f"  Successful: {result.successful_merges}")
    logger.info(f"  Failed: {len(result.failed_rows)}")
    logger.info(f"  Skipped: {len(result.skipped_rows)}")
    
    return result
