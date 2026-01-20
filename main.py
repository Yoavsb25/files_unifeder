#!/usr/bin/env python3
"""
Interactive interface for merging PDFs based on CSV serial numbers.
Prompts the user for all required parameters.
"""

import sys
from pathlib import Path

# Import the main processing function from merge_pdfs
from merge_pdfs import process_csv_row, parse_serial_numbers, find_pdf_file, merge_pdfs
import csv

try:
    import pandas as pd
except ImportError:
    pd = None


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


def validate_data_file(file_path: Path) -> bool:
    """Validate that the file exists and has the serial_numbers column."""
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    try:
        # Check if it's an Excel file
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            if pd is None:
                print("Error: pandas and openpyxl are required to read Excel files.")
                print("Install with: pip install pandas openpyxl")
                return False
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            if 'serial_numbers' not in df.columns:
                print(f"Error: 'serial_numbers' column not found in file.")
                print(f"Available columns: {', '.join(df.columns)}")
                return False
        else:
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                if 'serial_numbers' not in reader.fieldnames:
                    print(f"Error: 'serial_numbers' column not found in file.")
                    print(f"Available columns: {', '.join(reader.fieldnames)}")
                    return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    return True


def validate_folder(folder_path: Path, folder_type: str) -> bool:
    """Validate that the folder exists."""
    if not folder_path.exists():
        print(f"Error: {folder_type} folder not found: {folder_path}")
        return False
    
    if not folder_path.is_dir():
        print(f"Error: {folder_path} is not a directory")
        return False
    
    return True


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
        
        if validate_data_file(file_path):
            break
        print("Please try again.\n")
    
    # Get source folder path
    while True:
        folder_input = get_user_input("Enter path to folder containing PDF files")
        source_folder = Path(folder_input)
        
        if validate_folder(source_folder, "Source"):
            break
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
            print(f"Error creating output folder: {e}")
            print("Please try again.\n")
    
    print()
    print("=" * 60)
    print("Processing file...")
    print("=" * 60)
    print()
    
    # Process the file (CSV or Excel)
    try:
        # Check if it's an Excel file
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            if pd is None:
                print("Error: pandas and openpyxl are required to read Excel files.")
                print("Install with: pip install pandas openpyxl")
                sys.exit(1)
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            success_count = 0
            total_rows = 0
            
            for row_index, row in df.iterrows():
                total_rows += 1
                # Convert to string and handle NaN values
                serial_numbers_str = str(row.get('serial_numbers', '')) if pd.notna(row.get('serial_numbers')) else ''
                
                if process_csv_row(row_index, serial_numbers_str, source_folder, output_folder):
                    success_count += 1
        else:
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                success_count = 0
                total_rows = 0
                
                for row_index, row in enumerate(reader):
                    total_rows += 1
                    serial_numbers_str = row.get('serial_numbers', '')
                    
                    if process_csv_row(row_index, serial_numbers_str, source_folder, output_folder):
                        success_count += 1
        
        print()
        print("=" * 60)
        print("Processing complete!")
        print("=" * 60)
        print(f"Total rows processed: {total_rows}")
        print(f"Successfully merged PDFs: {success_count}")
        print(f"Output folder: {output_folder}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
