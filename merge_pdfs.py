#!/usr/bin/env python3
"""
Merge PDFs based on serial numbers from a CSV file.
Each row in the CSV produces one merged PDF document.
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader
    except ImportError:
        print("Error: pypdf or PyPDF2 library is required. Install with: pip install pypdf")
        sys.exit(1)


def parse_serial_numbers(serial_numbers_str: str) -> List[str]:
    """
    Parse comma-separated filenames (serial numbers) from a string.
    
    Args:
        serial_numbers_str: String containing comma-separated filenames
        
    Returns:
        List of filenames (stripped of whitespace)
    """
    if not serial_numbers_str or not serial_numbers_str.strip():
        return []
    
    # Split by comma and strip whitespace from each filename
    filenames = [s.strip() for s in serial_numbers_str.split(',')]
    # Filter out empty strings
    return [s for s in filenames if s]


def find_pdf_file(folder: Path, serial_number: str) -> Optional[Path]:
    """
    Find a PDF file matching the serial number (filename) in the given folder.
    
    Args:
        folder: Path to the folder containing PDF files
        serial_number: Filename (with or without .pdf extension) to search for
        
    Returns:
        Path to the PDF file if found, None otherwise
    """
    # If serial_number already has .pdf extension, try that first
    if serial_number.lower().endswith('.pdf'):
        pdf_path = folder / serial_number
        if pdf_path.exists():
            return pdf_path
    
    # Try with .pdf extension appended
    pdf_path = folder / f"{serial_number}.pdf"
    if pdf_path.exists():
        return pdf_path
    
    # Try case-insensitive search (exact filename match)
    serial_lower = serial_number.lower()
    for pdf_file in folder.glob("*.pdf"):
        if pdf_file.name.lower() == serial_lower or pdf_file.name.lower() == f"{serial_lower}.pdf":
            return pdf_file
        # Also try matching just the stem (filename without extension)
        if pdf_file.stem.lower() == serial_lower:
            return pdf_file
    
    return None


def merge_pdfs(pdf_paths: List[Path], output_path: Path) -> bool:
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path where the merged PDF will be saved
        
    Returns:
        True if successful, False otherwise
    """
    if not pdf_paths:
        print(f"Warning: No PDF files to merge for {output_path.name}")
        return False
    
    try:
        writer = PdfWriter()
        
        for pdf_path in pdf_paths:
            try:
                reader = PdfReader(str(pdf_path))
                # Add all pages from this PDF
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                print(f"Error reading PDF {pdf_path.name}: {e}")
                return False
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except Exception as e:
        print(f"Error merging PDFs to {output_path.name}: {e}")
        return False


def process_csv_row(row_index: int, serial_numbers_str: str, source_folder: Path, output_folder: Path) -> bool:
    """
    Process a single CSV row: find PDFs and merge them.
    
    Args:
        row_index: Index of the row (0-based, for naming output file)
        serial_numbers_str: Comma-separated filenames from the serial_numbers column
        source_folder: Folder containing the PDF files
        output_folder: Folder where merged PDFs will be saved
        
    Returns:
        True if successful, False otherwise
    """
    # Parse filenames from serial_numbers column
    filenames = parse_serial_numbers(serial_numbers_str)
    
    if not filenames:
        print(f"Row {row_index + 1}: No filenames found, skipping...")
        return False
    
    print(f"Row {row_index + 1}: Processing filenames: {', '.join(filenames)}")
    
    # Find PDF files for each filename
    pdf_paths = []
    missing_files = []
    
    for filename in filenames:
        pdf_path = find_pdf_file(source_folder, filename)
        if pdf_path:
            pdf_paths.append(pdf_path)
            print(f"  Found: {pdf_path.name}")
        else:
            missing_files.append(filename)
            print(f"  Warning: PDF file not found for filename '{filename}'")
    
    if not pdf_paths:
        print(f"Row {row_index + 1}: No PDF files found for any filenames, skipping...")
        return False
    
    # Create output filename
    output_filename = f"merged_row_{row_index + 1}.pdf"
    output_path = output_folder / output_filename
    
    # Merge PDFs
    print(f"  Merging {len(pdf_paths)} PDF(s) into {output_filename}...")
    success = merge_pdfs(pdf_paths, output_path)
    
    if success:
        print(f"  ✓ Successfully created {output_filename}")
    else:
        print(f"  ✗ Failed to create {output_filename}")
    
    return success


def main():
    """Main function to process CSV and merge PDFs."""
    parser = argparse.ArgumentParser(
        description="Merge PDFs based on serial numbers from a CSV file. Each row produces one merged PDF."
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Path to the CSV file containing serial_numbers column'
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
    
    # Validate paths
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    source_folder = Path(args.folder)
    if not source_folder.exists() or not source_folder.is_dir():
        print(f"Error: Source folder not found or is not a directory: {source_folder}")
        sys.exit(1)
    
    output_folder = Path(args.output)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Read CSV file
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Try to detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Check if serial_numbers column exists
            if 'serial_numbers' not in reader.fieldnames:
                print(f"Error: 'serial_numbers' column not found in CSV file.")
                print(f"Available columns: {', '.join(reader.fieldnames)}")
                sys.exit(1)
            
            # Process each row
            success_count = 0
            total_rows = 0
            
            for row_index, row in enumerate(reader):
                total_rows += 1
                serial_numbers_str = row.get('serial_numbers', '')
                
                if process_csv_row(row_index, serial_numbers_str, source_folder, output_folder):
                    success_count += 1
            
            print(f"\n{'='*60}")
            print(f"Processing complete!")
            print(f"Total rows processed: {total_rows}")
            print(f"Successfully merged PDFs: {success_count}")
            print(f"Output folder: {output_folder}")
            print(f"{'='*60}")
            
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
