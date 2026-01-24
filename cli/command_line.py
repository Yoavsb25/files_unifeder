"""
Command-line interface for PDF Merger.
Supports environment variables and configuration precedence.
"""

import argparse
import logging
import sys
from pathlib import Path

from pdf_merger import process_file, validate_paths
from pdf_merger.logger import setup_logger
from pdf_merger.exceptions import PDFMergerError
from pdf_merger.config import load_config

# Initialize logger for CLI
setup_logger("pdf_merger", level=logging.INFO)


def main():
    """Main function to process CSV/Excel and merge PDFs via command line."""
    parser = argparse.ArgumentParser(
        description="Merge PDFs based on serial numbers from a CSV or Excel file. Each row produces one merged PDF. "
                    "Configuration can be provided via environment variables, CLI arguments, config files, or per-project presets."
    )
    parser.add_argument(
        '--csv',
        required=False,
        help='Path to the CSV or Excel file (.csv, .xlsx, .xls) containing serial_numbers column. '
             'Can also be set via PDF_MERGER_INPUT_FILE environment variable.'
    )
    parser.add_argument(
        '--folder',
        required=False,
        help='Path to the folder containing PDF and Excel files. '
             'Can also be set via PDF_MERGER_SOURCE_DIR environment variable.'
    )
    parser.add_argument(
        '--output',
        required=False,
        help='Path to the output folder where merged PDFs will be saved. '
             'Can also be set via PDF_MERGER_OUTPUT_DIR environment variable.'
    )
    parser.add_argument(
        '--column',
        required=False,
        help='Name of the column containing serial numbers (default: serial_numbers). '
             'Can also be set via PDF_MERGER_COLUMN environment variable.'
    )
    
    args = parser.parse_args()
    
    # Load configuration with precedence: env > CLI > config > preset > defaults
    config = load_config(
        cli_input_file=args.csv,
        cli_source_dir=args.folder,
        cli_output_dir=args.output,
        cli_column=args.column,
        start_path=Path.cwd()
    )
    
    # Get paths from config or CLI args (CLI args take precedence if provided)
    file_path_str = args.csv or config.input_file
    source_folder_str = args.folder or config.pdf_dir
    output_folder_str = args.output or config.output_dir
    required_column = args.column or config.required_column
    
    # Validate that required paths are provided
    if not file_path_str:
        print("Error: Input file (--csv) is required or must be set via PDF_MERGER_INPUT_FILE environment variable")
        sys.exit(1)
    
    if not source_folder_str:
        print("Error: Source folder (--folder) is required or must be set via PDF_MERGER_SOURCE_DIR environment variable")
        sys.exit(1)
    
    if not output_folder_str:
        print("Error: Output folder (--output) is required or must be set via PDF_MERGER_OUTPUT_DIR environment variable")
        sys.exit(1)
    
    # Convert to Path objects
    file_path = Path(file_path_str)
    source_folder = Path(source_folder_str)
    output_folder = Path(output_folder_str)
    
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
    print(f"Input file: {file_path}")
    print(f"Source directory: {source_folder}")
    print(f"Output directory: {output_folder}")
    print(f"Column: {required_column}")
    print("=" * 60)
    print()
    
    result = process_file(file_path, source_folder, output_folder, required_column=required_column)
    
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
