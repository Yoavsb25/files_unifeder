"""
Command-line interface for PDF Merger.
"""

import argparse
import logging
import sys
from pathlib import Path

from pdf_merger import process_file, validate_paths
from pdf_merger.logger import setup_logger
from pdf_merger.exceptions import PDFMergerError

# Initialize logger for CLI
setup_logger("pdf_merger", level=logging.INFO)


def main():
    """Main function to process CSV/Excel and merge PDFs via command line."""
    parser = argparse.ArgumentParser(
        description="Merge PDFs based on serial numbers from a CSV or Excel file. Each row produces one merged PDF."
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Path to the CSV or Excel file (.csv, .xlsx, .xls) containing serial_numbers column'
    )
    parser.add_argument(
        '--folder',
        required=True,
        help='Path to the folder containing PDF files'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to the output folder where merged PDFs will be saved'
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    file_path = Path(args.csv)
    source_folder = Path(args.folder)
    output_folder = Path(args.output)
    
    # Validate paths (raises exceptions on failure)
    try:
        validate_paths(file_path, source_folder, output_folder)
    except PDFMergerError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    
    # Process the file
    print(f"\n{'='*60}")
    print("Processing file...")
    print("=" * 60)
    print()
    
    result = process_file(file_path, source_folder, output_folder)
    
    # Print summary
    print()
    print("=" * 60)
    print("Processing complete!")
    print("=" * 60)
    print(f"Total rows processed: {result.total_rows}")
    print(f"Successfully merged PDFs: {result.successful_merges}")
    print(f"Output folder: {output_folder}")
    if result.failed_rows:
        print(f"Failed rows: {', '.join(map(str, result.failed_rows))}")
    print("=" * 60)


if __name__ == '__main__':
    main()
