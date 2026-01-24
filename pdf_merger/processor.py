"""
Processor module.
Main orchestration logic for processing files and merging PDFs.
"""

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .pdf_operations import find_source_file, merge_pdfs
from .excel_converter import convert_excel_to_pdf
from .file_reader import read_data_file
from .logger import get_logger
from .exceptions import PDFMergerError, InvalidFileFormatError
from .enums import DEFAULT_SERIAL_NUMBERS_COLUMN, OUTPUT_FILENAME_PATTERN, EXCEL_FILE_EXTENSIONS
from .models import Row, MergeJob, MergeResult, RowResult, RowStatus

logger = get_logger("processor")


@dataclass
class ProcessingResult:
    """
    Result of processing a file.
    
    Note: This class is kept for backward compatibility.
    New code should use MergeResult from models package.
    """
    total_rows: int
    successful_merges: int
    failed_rows: List[int]
    
    def __str__(self) -> str:
        return (f"Total rows processed: {self.total_rows}\n"
                f"Successfully merged PDFs: {self.successful_merges}\n"
                f"Failed rows: {len(self.failed_rows)}")


def process_row(row_index: int, serial_numbers_str: str, source_folder: Path, 
                output_folder: Path) -> bool:
    """
    Process a single row: find PDFs and Excel files, convert Excel to PDF, and merge them.
    
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
    
    # Find all source files (PDFs and Excel files)
    source_files = []
    for serial_number in normalized_serial_numbers:
        source_path = find_source_file(source_folder, serial_number)
        if source_path:
            source_files.append(source_path)
            logger.info(f"  Found: {source_path.name}")
        else:
            logger.warning(f"  File not found for serial number '{serial_number}'")
    
    if not source_files:
        logger.warning(f"Row {row_index + 1}: No files found for any serial numbers, skipping...")
        return False
    
    # Convert Excel files to PDF and collect all PDF paths
    pdf_paths = []
    temp_pdf_files = []  # Track temporary files for cleanup
    
    try:
        for source_path in source_files:
            if source_path.suffix.lower() in EXCEL_FILE_EXTENSIONS:
                # Convert Excel to PDF
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
                    logger.info(f"  ✓ Converted {source_path.name} to PDF")
                else:
                    logger.error(f"  ✗ Failed to convert {source_path.name} to PDF")
            else:
                # Already a PDF file
                pdf_paths.append(source_path)
        
        if not pdf_paths:
            logger.warning(f"Row {row_index + 1}: No PDF files to merge (conversions may have failed), skipping...")
            return False
        
        output_filename = OUTPUT_FILENAME_PATTERN.format(row_index + 1)
        output_path = output_folder / output_filename
        
        logger.info(f"  Merging {len(pdf_paths)} file(s) into {output_filename}...")
        success = merge_pdfs(pdf_paths, output_path)
        
        if success:
            logger.info(f"  ✓ Successfully created {output_filename}")
        else:
            logger.error(f"  ✗ Failed to create {output_filename}")
        
        return success
        
    finally:
        # Clean up temporary PDF files
        for temp_pdf in temp_pdf_files:
            try:
                if temp_pdf.exists():
                    temp_pdf.unlink()
                    logger.debug(f"  Cleaned up temporary file: {temp_pdf.name}")
            except Exception as e:
                logger.warning(f"  Failed to clean up temporary file {temp_pdf.name}: {e}")


def process_row_with_models(row: Row, source_folder: Path, output_folder: Path) -> RowResult:
    """
    Process a single row using domain models: find PDFs and Excel files, convert Excel to PDF, and merge them.
    
    Args:
        row: Row instance to process
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        
    Returns:
        RowResult with processing details
    """
    start_time = time.time()
    
    if not row.has_serial_numbers():
        logger.warning(f"Row {row.row_index + 1}: No valid serial numbers, skipping...")
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            error_message="No valid serial numbers found"
        )
    
    logger.info(f"Row {row.row_index + 1}: Processing serial numbers: {', '.join(row.serial_numbers)}")
    
    # Find all source files (PDFs and Excel files)
    source_files = []
    missing_serial_numbers = []
    
    for serial_number in row.serial_numbers:
        source_path = find_source_file(source_folder, serial_number)
        if source_path:
            source_files.append(source_path)
            logger.info(f"  Found: {source_path.name}")
        else:
            missing_serial_numbers.append(serial_number)
            logger.warning(f"  File not found for serial number '{serial_number}'")
    
    if not source_files:
        logger.warning(f"Row {row.row_index + 1}: No files found for any serial numbers, skipping...")
        return RowResult(
            row_index=row.row_index,
            status=RowStatus.SKIPPED,
            files_missing=missing_serial_numbers,
            error_message="No source files found"
        )
    
    # Convert Excel files to PDF and collect all PDF paths
    pdf_paths = []
    temp_pdf_files = []  # Track temporary files for cleanup
    
    try:
        for source_path in source_files:
            if source_path.suffix.lower() in EXCEL_FILE_EXTENSIONS:
                # Convert Excel to PDF
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
                    logger.info(f"  ✓ Converted {source_path.name} to PDF")
                else:
                    logger.error(f"  ✗ Failed to convert {source_path.name} to PDF")
            else:
                # Already a PDF file
                pdf_paths.append(source_path)
        
        if not pdf_paths:
            logger.warning(f"Row {row.row_index + 1}: No PDF files to merge (conversions may have failed), skipping...")
            return RowResult(
                row_index=row.row_index,
                status=RowStatus.FAILED,
                files_found=source_files,
                files_missing=missing_serial_numbers,
                error_message="No PDF files available for merging"
            )
        
        output_filename = OUTPUT_FILENAME_PATTERN.format(row.row_index + 1)
        output_path = output_folder / output_filename
        
        logger.info(f"  Merging {len(pdf_paths)} file(s) into {output_filename}...")
        success = merge_pdfs(pdf_paths, output_path)
        
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
                processing_time=processing_time
            )
        else:
            logger.error(f"  ✗ Failed to create {output_filename}")
            return RowResult(
                row_index=row.row_index,
                status=RowStatus.FAILED,
                files_found=source_files,
                files_missing=missing_serial_numbers,
                error_message="Failed to merge PDFs",
                processing_time=processing_time
            )
        
    finally:
        # Clean up temporary PDF files
        for temp_pdf in temp_pdf_files:
            try:
                if temp_pdf.exists():
                    temp_pdf.unlink()
                    logger.debug(f"  Cleaned up temporary file: {temp_pdf.name}")
            except Exception as e:
                logger.warning(f"  Failed to clean up temporary file {temp_pdf.name}: {e}")


def process_job(job: MergeJob) -> MergeResult:
    """
    Process a merge job using domain models.
    
    Args:
        job: MergeJob instance to process
        
    Returns:
        MergeResult with detailed processing results
    """
    job.output_folder.mkdir(parents=True, exist_ok=True)
    
    result = MergeResult(
        total_rows=job.get_total_rows(),
        successful_merges=0,
        job_id=job.job_id
    )
    
    start_time = time.time()
    
    try:
        for row in job.rows:
            row_result = process_row_with_models(row, job.source_folder, job.output_folder)
            result.add_row_result(row_result)
        
        result.total_processing_time = time.time() - start_time
        logger.info(f"Job {job.job_id or 'default'} completed: {result}")
        return result
        
    except PDFMergerError as e:
        logger.error(f"PDF Merger error: {e}")
        result.total_processing_time = time.time() - start_time
        return result
    except Exception as e:
        logger.error(f"Unexpected error processing job: {e}")
        result.total_processing_time = time.time() - start_time
        return result


def process_file(file_path: Path, source_folder: Path, output_folder: Path,
                 required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN) -> ProcessingResult:
    """
    Process an entire data file and merge PDFs and Excel files for each row.
    
    Note: This function is kept for backward compatibility.
    New code should use process_job() with MergeJob domain model.
    
    Args:
        file_path: Path to the CSV or Excel file
        source_folder: Folder containing the PDF and Excel files
        output_folder: Folder where merged PDFs will be saved
        required_column: Name of the column containing serial numbers
        
    Returns:
        ProcessingResult with statistics about the processing
    """
    # Use domain models internally but return legacy result
    job = MergeJob.create(
        input_file=file_path,
        source_folder=source_folder,
        output_folder=output_folder,
        required_column=required_column
    )
    
    # Load rows from file
    try:
        for row_index, row_data in enumerate(read_data_file(file_path), start=0):
            row = Row.from_raw_data(row_index, row_data, required_column)
            job.add_row(row)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return ProcessingResult(total_rows=0, successful_merges=0, failed_rows=[])
    
    # Process job
    merge_result = process_job(job)
    
    # Convert to legacy result
    return ProcessingResult(
        total_rows=merge_result.total_rows,
        successful_merges=merge_result.successful_merges,
        failed_rows=merge_result.failed_rows
    )
