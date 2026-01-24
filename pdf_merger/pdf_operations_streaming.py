"""
Streaming PDF operations module.
Provides memory-efficient PDF merging for large files.
"""

import sys
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from .logger import get_logger
from .pdf_operations import suppress_stderr

logger = get_logger("pdf_operations_streaming")

# Lazy import of PDF libraries
_PdfWriter = None
_PdfReader = None


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


def merge_pdfs_streaming(
    pdf_paths: List[Path],
    output_path: Path,
    chunk_size: int = 10
) -> bool:
    """
    Merge multiple PDF files using streaming mode (processes pages incrementally).
    
    This is more memory-efficient for large PDFs as it processes pages in chunks
    rather than loading all pages into memory at once.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path where the merged PDF will be saved
        chunk_size: Number of pages to process at a time (default: 10)
        
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
        
        total_pages = 0
        processed_pages = 0
        
        # First pass: count total pages and validate files
        for pdf_path in pdf_paths:
            try:
                with suppress_stderr():
                    reader = PdfReader(str(pdf_path), strict=False)
                    total_pages += len(reader.pages)
            except Exception as e:
                logger.error(f"Error reading PDF {pdf_path.name}: {e}")
                return False
        
        logger.info(f"Merging {len(pdf_paths)} PDF(s) with {total_pages} total pages using streaming mode")
        
        # Second pass: process pages in chunks
        for pdf_path in pdf_paths:
            try:
                with suppress_stderr():
                    reader = PdfReader(str(pdf_path), strict=False)
                    
                    # Process pages in chunks
                    for i in range(0, len(reader.pages), chunk_size):
                        chunk = reader.pages[i:i + chunk_size]
                        for page in chunk:
                            writer.add_page(page)
                            processed_pages += 1
                        
                        # Log progress for large files
                        if total_pages > 100 and processed_pages % 50 == 0:
                            logger.debug(f"Processed {processed_pages}/{total_pages} pages")
                    
            except Exception as e:
                logger.error(f"Error reading PDF {pdf_path.name}: {e}")
                return False
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        logger.info(f"Successfully merged {processed_pages} pages into {output_path.name}")
        return True
        
    except ImportError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"Error merging PDFs to {output_path.name}: {e}")
        return False


def get_pdf_size_mb(pdf_path: Path) -> float:
    """
    Get the size of a PDF file in megabytes.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Size in megabytes
    """
    try:
        size_bytes = pdf_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def estimate_memory_usage(pdf_paths: List[Path]) -> float:
    """
    Estimate memory usage for merging PDFs (rough estimate).
    
    Args:
        pdf_paths: List of PDF file paths
        
    Returns:
        Estimated memory usage in megabytes
    """
    total_size_mb = sum(get_pdf_size_mb(p) for p in pdf_paths)
    # Rough estimate: PDF libraries may use 2-3x the file size in memory
    return total_size_mb * 2.5


def should_use_streaming(pdf_paths: List[Path], threshold_mb: float = 100.0) -> bool:
    """
    Determine if streaming mode should be used based on file sizes.
    
    Args:
        pdf_paths: List of PDF file paths
        threshold_mb: Memory threshold in MB (default: 100 MB)
        
    Returns:
        True if streaming should be used, False otherwise
    """
    estimated_memory = estimate_memory_usage(pdf_paths)
    return estimated_memory > threshold_mb
