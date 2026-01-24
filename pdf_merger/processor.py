"""
Processor module.
Main orchestration logic for processing files and merging PDFs.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .pdf_operations import find_pdf_file, merge_pdfs
from .data_parser import (
    split_serial_numbers,
    deduplicate_serial_numbers,
    normalize_serial_number
)
from .file_reader import read_data_file
from .logger import get_logger
from .exceptions import PDFMergerError, InvalidFileFormatError
from .enums import DEFAULT_SERIAL_NUMBERS_COLUMN, OUTPUT_FILENAME_PATTERN
from .validators import validate_serial_number

logger = get_logger("processor")


@dataclass
class ProcessingResult:
    """Result of processing a file."""
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
    Process a single row: find PDFs and merge them.
    
    Args:
        row_index: Index of the row (0-based, for naming output file)
        serial_numbers_str: Comma-separated filenames from the serial_numbers column
        source_folder: Folder containing the PDF files
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
    
    pdf_paths = []
    for serial_number in normalized_serial_numbers:
        pdf_path = find_pdf_file(source_folder, serial_number)
        if pdf_path:
            pdf_paths.append(pdf_path)
            logger.info(f"  Found: {pdf_path.name}")
        else:
            logger.warning(f"  PDF file not found for serial number '{serial_number}'")
    
    if not pdf_paths:
        logger.warning(f"Row {row_index + 1}: No PDF files found for any serial numbers, skipping...")
        return False
    
    output_filename = OUTPUT_FILENAME_PATTERN.format(row_index + 1)
    output_path = output_folder / output_filename
    
    logger.info(f"  Merging {len(pdf_paths)} PDF(s) into {output_filename}...")
    success = merge_pdfs(pdf_paths, output_path)
    
    if success:
        logger.info(f"  ✓ Successfully created {output_filename}")
    else:
        logger.error(f"  ✗ Failed to create {output_filename}")
    
    return success


def process_file(file_path: Path, source_folder: Path, output_folder: Path,
                 required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN) -> ProcessingResult:
    """
    Process an entire data file and merge PDFs for each row.
    
    Args:
        file_path: Path to the CSV or Excel file
        source_folder: Folder containing the PDF files
        output_folder: Folder where merged PDFs will be saved
        required_column: Name of the column containing serial numbers
        
    Returns:
        ProcessingResult with statistics about the processing
    """
    output_folder.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    row_index = 0
    failed_rows = []
    
    try:
        for row_index, row in enumerate(read_data_file(file_path), start=1):
            serial_numbers_str = row.get(required_column, '')
            
            if process_row(row_index, serial_numbers_str, source_folder, output_folder):
                success_count += 1
            else:
                failed_rows.append(row_index)
        
        return ProcessingResult(
            total_rows=row_index,
            successful_merges=success_count,
            failed_rows=failed_rows
        )
    except PDFMergerError as e:
        logger.error(f"PDF Merger error: {e}")
        return ProcessingResult(
            total_rows=row_index,
            successful_merges=success_count,
            failed_rows=failed_rows
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        return ProcessingResult(
            total_rows=row_index,
            successful_merges=success_count,
            failed_rows=failed_rows
        )
