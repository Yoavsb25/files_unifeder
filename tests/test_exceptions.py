"""
Unit tests for exceptions module.
"""

import pytest
from pathlib import Path
from pdf_merger.exceptions import (
    PDFMergerError,
    FileNotFoundError,
    InvalidFileFormatError,
    MissingColumnError,
    PDFProcessingError,
    ValidationError
)


class TestPDFMergerError:
    """Test cases for PDFMergerError base class."""
    
    def test_pdf_merger_error_creation(self):
        """Test creating a PDFMergerError."""
        error = PDFMergerError("Test error message")
        
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
    
    def test_pdf_merger_error_inheritance(self):
        """Test that PDFMergerError inherits from Exception."""
        error = PDFMergerError("Test error")
        
        assert isinstance(error, Exception)


class TestFileNotFoundError:
    """Test cases for FileNotFoundError."""
    
    def test_file_not_found_error_with_path(self):
        """Test creating FileNotFoundError with path."""
        path = Path("/nonexistent/file.txt")
        error = FileNotFoundError(path)
        
        assert error.path == path
        assert error.file_type == "File"
        assert "File not found" in str(error)
        assert str(path) in str(error)
    
    def test_file_not_found_error_with_custom_type(self):
        """Test creating FileNotFoundError with custom file type."""
        path = Path("/nonexistent/folder")
        error = FileNotFoundError(path, file_type="Source folder")
        
        assert error.path == path
        assert error.file_type == "Source folder"
        assert "Source folder not found" in str(error)
    
    def test_file_not_found_error_with_string_path(self):
        """Test creating FileNotFoundError with string path."""
        path_str = "/nonexistent/file.txt"
        error = FileNotFoundError(path_str)
        
        assert isinstance(error.path, Path)
        assert str(error.path) == path_str


class TestInvalidFileFormatError:
    """Test cases for InvalidFileFormatError."""
    
    def test_invalid_file_format_error_without_path(self):
        """Test creating InvalidFileFormatError without file path."""
        error = InvalidFileFormatError("Invalid format")
        
        assert error.file_path is None
        assert str(error) == "Invalid format"
    
    def test_invalid_file_format_error_with_path(self):
        """Test creating InvalidFileFormatError with file path."""
        path = Path("/path/to/file.csv")
        error = InvalidFileFormatError("Invalid format", file_path=path)
        
        assert error.file_path == path
        assert "Invalid format" in str(error)
        assert str(path) in str(error)
    
    def test_invalid_file_format_error_with_string_path(self):
        """Test creating InvalidFileFormatError with string path."""
        path_str = "/path/to/file.csv"
        error = InvalidFileFormatError("Invalid format", file_path=path_str)
        
        assert isinstance(error.file_path, Path)
        assert str(error.file_path) == path_str


class TestMissingColumnError:
    """Test cases for MissingColumnError."""
    
    def test_missing_column_error_without_path(self):
        """Test creating MissingColumnError without file path."""
        error = MissingColumnError(
            "serial_numbers",
            ["col1", "col2", "col3"]
        )
        
        assert error.column_name == "serial_numbers"
        assert error.available_columns == ["col1", "col2", "col3"]
        assert error.file_path is None
        assert "serial_numbers" in str(error)
        assert "col1, col2, col3" in str(error)
    
    def test_missing_column_error_with_path(self):
        """Test creating MissingColumnError with file path."""
        path = Path("/path/to/file.csv")
        error = MissingColumnError(
            "serial_numbers",
            ["col1", "col2"],
            file_path=path
        )
        
        assert error.file_path == path
        assert str(path) in str(error)
    
    def test_missing_column_error_empty_columns(self):
        """Test creating MissingColumnError with empty columns list."""
        error = MissingColumnError("serial_numbers", [])
        
        assert error.available_columns == []
        assert "(no columns found)" in str(error)


class TestPDFProcessingError:
    """Test cases for PDFProcessingError."""
    
    def test_pdf_processing_error_basic(self):
        """Test creating PDFProcessingError with just a message."""
        error = PDFProcessingError("Processing failed")
        
        assert error.pdf_path is None
        assert error.operation is None
        assert str(error) == "Processing failed"
    
    def test_pdf_processing_error_with_path(self):
        """Test creating PDFProcessingError with PDF path."""
        path = Path("/path/to/file.pdf")
        error = PDFProcessingError("Processing failed", pdf_path=path)
        
        assert error.pdf_path == path
        assert "file.pdf" in str(error)
        assert "Processing failed" in str(error)
    
    def test_pdf_processing_error_with_operation(self):
        """Test creating PDFProcessingError with operation."""
        error = PDFProcessingError("Processing failed", operation="reading")
        
        assert error.operation == "reading"
        assert "Error reading PDF" in str(error)
    
    def test_pdf_processing_error_with_all_fields(self):
        """Test creating PDFProcessingError with all fields."""
        path = Path("/path/to/file.pdf")
        error = PDFProcessingError(
            "Processing failed",
            pdf_path=path,
            operation="merging"
        )
        
        assert error.pdf_path == path
        assert error.operation == "merging"
        assert "Error merging PDF" in str(error)
        assert "file.pdf" in str(error)


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_validation_error_basic(self):
        """Test creating ValidationError with just a message."""
        error = ValidationError("Validation failed")
        
        assert error.field is None
        assert "Validation failed" in str(error)
    
    def test_validation_error_with_field(self):
        """Test creating ValidationError with field name."""
        error = ValidationError("Invalid value", field="serial_number")
        
        assert error.field == "serial_number"
        assert "serial_number" in str(error)
        assert "Invalid value" in str(error)
