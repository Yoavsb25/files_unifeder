"""
PDF operations module.
Handles finding and merging PDF files.
"""

import sys
import os
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from .logger import get_logger
from .enums import PDF_FILE_EXTENSION, SOURCE_FILE_EXTENSIONS, EXCEL_FILE_EXTENSIONS

logger = get_logger("pdf_operations")

# Lazy import of PDF libraries - only import when merge_pdfs is called
_PdfWriter = None
_PdfReader = None


@contextmanager
def suppress_stderr():
    """Context manager to suppress stderr output."""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        try:
            sys.stderr = devnull
            yield
        finally:
            sys.stderr = old_stderr


def _get_pdf_libraries():
    """
    Lazy import of PDF libraries.
    Raises ImportError if neither pypdf nor PyPDF2 is available.
    """
    global _PdfWriter, _PdfReader
    
    if _PdfWriter is None or _PdfReader is None:
        try:
            from pypdf import PdfWriter, PdfReader
            _PdfWriter = PdfWriter
            _PdfReader = PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfWriter, PdfReader
                _PdfWriter = PdfWriter
                _PdfReader = PdfReader
            except ImportError:
                raise ImportError(
                    "pypdf or PyPDF2 library is required. Install with: pip install pypdf"
                )
    
    return _PdfWriter, _PdfReader


def find_source_file(folder: Path, filename: str) -> Optional[Path]:
    """
    Find a source file (PDF or Excel) matching the filename in the given folder.
    Searches for PDF files first, then Excel files.
    
    Args:
        folder: Path to the folder containing source files
        filename: Filename (with or without extension) to search for
        
    Returns:
        Path to the source file if found, None otherwise
    """
    filename_lower = filename.lower()
    filename_stem = Path(filename).stem.lower()
    
    # Try exact match first (with any supported extension)
    for ext in SOURCE_FILE_EXTENSIONS:
        file_path = folder / f"{filename_lower}{ext}"
        if file_path.exists():
            return file_path
    
    # Try matching by stem (filename without extension)
    for source_file in folder.iterdir():
        if not source_file.is_file():
            continue
        
        file_ext = source_file.suffix.lower()
        if file_ext not in SOURCE_FILE_EXTENSIONS:
            continue
        
        # Match by full filename (case-insensitive)
        if source_file.name.lower() == filename_lower:
            return source_file
        
        # Match by stem (filename without extension)
        if source_file.stem.lower() == filename_stem or source_file.stem.lower() == filename_lower:
            return source_file
    
    return None


def find_pdf_file(folder: Path, filename: str) -> Optional[Path]:
    """
    Find a PDF file matching the filename in the given folder.
    
    This function is kept for backward compatibility.
    For finding both PDF and Excel files, use find_source_file() instead.
    
    Args:
        folder: Path to the folder containing PDF files
        filename: Filename (with or without .pdf extension) to search for
        
    Returns:
        Path to the PDF file if found, None otherwise
    """
    # If filename already has .pdf extension, try that first
    filename_lower = filename.lower()
    if filename_lower.endswith(PDF_FILE_EXTENSION):
        pdf_path = folder / filename
        if pdf_path.exists():
            return pdf_path
    
    # Try with .pdf extension appended
    pdf_path = folder / f"{filename_lower}{PDF_FILE_EXTENSION}"
    if pdf_path.exists():
        return pdf_path
    
    # Try case-insensitive search (exact filename match)
    for pdf_file in folder.glob(f"*{PDF_FILE_EXTENSION}"):
        if pdf_file.name.lower() == filename_lower or pdf_file.name.lower() == f"{filename_lower}{PDF_FILE_EXTENSION}":
            return pdf_file
        # Also try matching just the stem (filename without extension)
        if pdf_file.stem.lower() == filename_lower:
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
        
    Raises:
        ImportError: If pypdf or PyPDF2 is not installed
    """
    if not pdf_paths:
        logger.warning(f"No PDF files to merge for {output_path.name}")
        return False
    
    try:
        PdfWriter, PdfReader = _get_pdf_libraries()
        writer = PdfWriter()
        
        for pdf_path in pdf_paths:
            try:
                # Suppress stderr during PDF reading to avoid noisy PdfReadError messages
                # These are common with Apple-annotated PDFs but don't prevent successful reading
                # when strict=False is used
                with suppress_stderr():
                    reader = PdfReader(str(pdf_path), strict=False)
                    for page in reader.pages:
                        writer.add_page(page)
            except Exception as e:
                logger.error(f"Error reading PDF {pdf_path.name}: {e}")
                return False
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except ImportError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"Error merging PDFs to {output_path.name}: {e}")
        return False
