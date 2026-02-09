"""
Custom exceptions for PDF Merger.
Provides specific exception types for different error conditions.
"""

from pathlib import Path
from typing import Optional, List


class PDFMergerError(Exception):
    """
    Base exception for all PDF Merger errors.
    
    All custom exceptions inherit from this class, allowing for
    catching all PDF Merger specific errors with a single except clause.
    """
    
    def __init__(self, message: str):
        """
        Initialize PDFMergerError.
        
        Args:
            message: Error message describing what went wrong
        """
        self.message = message
        super().__init__(self.message)


class PathNotFoundError(PDFMergerError):
    """
    Raised when a required file or folder is not found.

    This exception provides detailed information about what file or folder
    was expected but not found. Named PathNotFoundError to avoid shadowing
    Python's built-in FileNotFoundError.
    """

    def __init__(self, path: Path, file_type: str = "File"):
        """
        Initialize PathNotFoundError.

        Args:
            path: Path to the file or folder that was not found
            file_type: Type description (e.g., "File", "Folder", "Source folder")
        """
        self.path = Path(path) if not isinstance(path, Path) else path
        self.file_type = file_type
        message = f"{file_type} not found: {self.path}"
        super().__init__(message)


class InvalidFileFormatError(PDFMergerError):
    """
    Raised when file format is unsupported or invalid.
    
    This exception is raised when attempting to read a file with an
    unsupported format or when the file format is corrupted.
    """
    
    def __init__(self, message: str, file_path: Optional[Path] = None):
        """
        Initialize InvalidFileFormatError.
        
        Args:
            message: Error message describing the format issue
            file_path: Optional path to the file that caused the error
        """
        self.file_path = Path(file_path) if file_path and not isinstance(file_path, Path) else file_path
        if self.file_path:
            full_message = f"{message} (File: {self.file_path})"
        else:
            full_message = message
        super().__init__(full_message)


class MissingColumnError(PDFMergerError):
    """
    Raised when required column is missing from data file.
    
    This exception provides information about which column was expected
    and what columns are actually available in the file.
    """
    
    def __init__(self, column_name: str, available_columns: List[str], file_path: Optional[Path] = None):
        """
        Initialize MissingColumnError.
        
        Args:
            column_name: Name of the missing column
            available_columns: List of available columns in the file
            file_path: Optional path to the file that's missing the column
        """
        self.column_name = column_name
        self.available_columns = available_columns
        self.file_path = Path(file_path) if file_path and not isinstance(file_path, Path) else file_path
        
        columns_str = ', '.join(available_columns) if available_columns else '(no columns found)'
        message = f"Required column '{column_name}' not found"
        
        if self.file_path:
            message += f" in file: {self.file_path}"
        
        message += f". Available columns: {columns_str}"
        
        super().__init__(message)


class PDFProcessingError(PDFMergerError):
    """
    Raised when PDF operations fail (reading, merging, writing).
    
    This exception is raised when there are issues with PDF operations
    such as reading a PDF file, merging multiple PDFs, or writing the
    merged output.
    """
    
    def __init__(self, message: str, pdf_path: Optional[Path] = None, operation: Optional[str] = None):
        """
        Initialize PDFProcessingError.
        
        Args:
            message: Error message describing the PDF operation failure
            pdf_path: Optional path to the PDF file that caused the error
            operation: Optional description of the operation (e.g., "reading", "merging", "writing")
        """
        self.pdf_path = Path(pdf_path) if pdf_path and not isinstance(pdf_path, Path) else pdf_path
        self.operation = operation
        
        # Build informative error message
        parts = []
        if self.operation:
            parts.append(f"Error {self.operation} PDF")
        if self.pdf_path:
            parts.append(f"'{self.pdf_path.name}'")
        if parts:
            full_message = " ".join(parts) + f": {message}"
        else:
            full_message = message
        
        super().__init__(full_message)


class ValidationError(PDFMergerError):
    """
    Raised for general validation failures.
    
    This exception is raised when validation checks fail, such as
    invalid file paths, missing required data, or invalid configurations.
    """
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize ValidationError.
        
        Args:
            message: Error message describing the validation failure
            field: Optional name of the field or value that failed validation
        """
        self.field = field
        
        if self.field:
            full_message = f"Validation failed for '{self.field}': {message}"
        else:
            full_message = f"Validation failed: {message}"
        
        super().__init__(full_message)
