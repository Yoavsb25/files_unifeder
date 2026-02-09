"""
PDF merger module.
Handles finding and merging PDF files.
"""

import sys
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from ..utils.logging_utils import get_logger
from ..core.constants import Constants

logger = get_logger("pdf_merger")

# Module-level constants
PDF_FILE_EXTENSION = Constants.PDF_FILE_EXTENSION
STREAMING_THRESHOLD_MB = Constants.STREAMING_THRESHOLD_MB

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


def find_source_file(
    folder: Path,
    filename: str,
    fail_on_ambiguous: bool = False
) -> Optional[Path]:
    """
    Find a source file (PDF or Excel) matching the filename in the given folder.
    Uses formal matching rules with ambiguity detection.
    
    Args:
        folder: Path to the folder containing source files
        filename: Filename (with or without extension) to search for
        fail_on_ambiguous: If True, raises ValueError on ambiguous matches (default: False)
        
    Returns:
        Path to the source file if found, None otherwise
        
    Raises:
        ValueError: If fail_on_ambiguous is True and multiple matches are found
    """
    from ..matching import find_best_match, MatchBehavior
    
    behavior = MatchBehavior.FAIL_FAST if fail_on_ambiguous else MatchBehavior.WARN_FIRST
    
    try:
        match_result = find_best_match(folder, filename, behavior=behavior)
        return match_result.file_path
    except ValueError as e:
        # Re-raise ValueError from matching rules
        raise


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


def merge_pdfs(
    pdf_paths: List[Path],
    output_path: Path,
    use_streaming: Optional[bool] = None,
    streaming_threshold_mb: float = STREAMING_THRESHOLD_MB
) -> bool:
    """
    Merge multiple PDF files into a single PDF.
    
    Automatically uses streaming mode for large files to conserve memory.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path where the merged PDF will be saved
        use_streaming: Force streaming mode (None = auto-detect based on file size)
        streaming_threshold_mb: Memory threshold in MB for auto-enabling streaming (default: 100 MB)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        ImportError: If pypdf or PyPDF2 is not installed
    """
    if not pdf_paths:
        logger.warning(f"No PDF files to merge for {output_path.name}")
        return False
    
    # Auto-detect streaming mode if not specified
    if use_streaming is None:
        try:
            from .streaming_pdf_merger import should_use_streaming
            use_streaming = should_use_streaming(pdf_paths, streaming_threshold_mb)
            if use_streaming:
                logger.info(f"Using streaming mode for large PDF merge (estimated size > {streaming_threshold_mb} MB)")
        except ImportError:
            use_streaming = False
    
    # Use streaming mode for large files
    if use_streaming:
        try:
            from .streaming_pdf_merger import merge_pdfs_streaming
            return merge_pdfs_streaming(pdf_paths, output_path)
        except ImportError:
            logger.warning("Streaming mode requested but not available, falling back to standard mode")
    
    # Standard mode (load all pages into memory)
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
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return True
    except ImportError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"Error merging PDFs to {output_path.name}: {e}")
        return False
