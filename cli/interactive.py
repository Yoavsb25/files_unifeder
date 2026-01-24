"""
Interactive interface for PDF Merger.
Prompts the user for all required parameters.
"""

import logging
import sys
from pathlib import Path

from pdf_merger import process_file, validate_file, validate_folder
from pdf_merger.logger import setup_logger
from pdf_merger.exceptions import PDFMergerError

# Initialize logger for interactive mode
setup_logger("pdf_merger", level=logging.INFO)


def get_user_input(prompt: str, default: str = None) -> str:
    """
    Get input from user with optional default value.
    
    Args:
        prompt: Prompt message to display
        default: Optional default value
        
    Returns:
        User input string
    """
    if default:
        full_prompt = f"{prompt} (default: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    user_input = input(full_prompt).strip()
    
    if not user_input and default:
        return default
    
    return user_input


def main():
    """Main interactive function."""
    print("=" * 60)
    print("PDF Merger - Interactive Mode")
    print("=" * 60)
    print()
    
    # Get data file path (CSV or Excel)
    while True:
        file_input = get_user_input("Enter path to CSV or Excel file (.csv, .xlsx, .xls)")
        file_path = Path(file_input)
        
        try:
            validate_file(file_path)
            break
        except PDFMergerError as e:
            print(f"Error: {e}")
            print("Please try again.\n")
    
    # Get source folder path
    while True:
        folder_input = get_user_input("Enter path to folder containing PDF files")
        source_folder = Path(folder_input)
        
        try:
            validate_folder(source_folder, "Source")
            break
        except PDFMergerError as e:
            print(f"Error: {e}")
            print("Please try again.\n")
    
    # Get output folder path
    while True:
        output_input = get_user_input("Enter path to output folder (will be created if it doesn't exist)")
        output_folder = Path(output_input)
        
        # Create output folder if it doesn't exist
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
            break
        except Exception as e:
            logger = logging.getLogger("pdf_merger")
            logger.error(f"Error creating output folder: {e}")
            print(f"Error creating output folder: {e}")
            print("Please try again.\n")
    
    print()
    print("=" * 60)
    print("Processing file...")
    print("=" * 60)
    print()
    
    # Process the file
    try:
        result = process_file(file_path, source_folder, output_folder)
        
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
        
    except Exception as e:
        logger = logging.getLogger("pdf_merger")
        logger.error(f"Error processing file: {e}")
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
