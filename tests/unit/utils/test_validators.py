"""
Unit tests for validators module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.utils.validators import (
    validate_serial_number,
    validate_folder,
    validate_file,
    validate_paths
)
from pdf_merger.utils.exceptions import PDFMergerFileNotFoundError, MissingColumnError, ValidationError, InvalidFileFormatError


class TestValidateSerialNumber:
    """Test cases for validate_serial_number function."""
    
    def test_valid_uppercase_serial_number(self):
        """Test validation of valid uppercase serial number."""
        assert validate_serial_number("GRNW_000103851") is True
    
    def test_valid_lowercase_serial_number(self):
        """Test validation of valid lowercase serial number."""
        assert validate_serial_number("grnw_000103851") is True
    
    def test_invalid_no_prefix(self):
        """Test validation of serial number without prefix."""
        assert validate_serial_number("000103851") is False
    
    def test_invalid_wrong_prefix(self):
        """Test validation of serial number with wrong prefix."""
        assert validate_serial_number("WRONG_000103851") is False
    
    def test_invalid_empty_string(self):
        """Test validation of empty string."""
        assert validate_serial_number("") is False
    
    def test_invalid_whitespace_only(self):
        """Test validation of whitespace-only string."""
        assert validate_serial_number("   ") is False
    
    def test_invalid_none(self):
        """Test validation of None."""
        assert validate_serial_number(None) is False


class TestValidateFolder:
    """Test cases for validate_folder function."""
    
    def test_valid_existing_folder(self, tmp_path):
        """Test validation of existing folder."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        # Should not raise exception
        validate_folder(folder)
    
    def test_invalid_nonexistent_folder(self, tmp_path):
        """Test validation of non-existent folder."""
        folder = tmp_path / "nonexistent"
        with pytest.raises(PDFMergerFileNotFoundError) as exc_info:
            validate_folder(folder)
        assert "nonexistent" in str(exc_info.value)
    
    def test_invalid_file_not_folder(self, tmp_path):
        """Test validation when path is a file, not a folder."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test")
        with pytest.raises(PDFMergerFileNotFoundError) as exc_info:
            validate_folder(file_path)
        assert "not a directory" in str(exc_info.value)
    
    def test_custom_folder_type(self, tmp_path):
        """Test validation with custom folder type."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        # Should not raise exception
        validate_folder(folder, "Source")


class TestValidateFile:
    """Test cases for validate_file function."""
    
    @patch('pdf_merger.utils.validators.get_file_columns')
    def test_valid_file_with_required_column(self, mock_get_columns, tmp_path):
        """Test validation of file with required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("serial_numbers,other\nGRNW_001,value")
        mock_get_columns.return_value = ["serial_numbers", "other"]
        
        # Should not raise exception
        validate_file(file_path)
        mock_get_columns.assert_called_once_with(file_path)
    
    @patch('pdf_merger.utils.validators.get_file_columns')
    def test_invalid_file_missing_column(self, mock_get_columns, tmp_path):
        """Test validation of file missing required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("other,value\nvalue1,value2")
        mock_get_columns.return_value = ["other", "value"]
        
        with pytest.raises(MissingColumnError) as exc_info:
            validate_file(file_path)
        assert exc_info.value.column_name == "serial_numbers"
        assert "other" in exc_info.value.available_columns
    
    @patch('pdf_merger.utils.validators.get_file_columns')
    def test_invalid_nonexistent_file(self, mock_get_columns, tmp_path):
        """Test validation of non-existent file."""
        file_path = tmp_path / "nonexistent.csv"
        mock_get_columns.return_value = []
        
        with pytest.raises(PDFMergerFileNotFoundError) as exc_info:
            validate_file(file_path)
        assert "nonexistent.csv" in str(exc_info.value)
        mock_get_columns.assert_not_called()
    
    @patch('pdf_merger.utils.validators.get_file_columns')
    def test_invalid_file_read_error(self, mock_get_columns, tmp_path):
        """Test validation when file reading raises an error."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("test")
        mock_get_columns.side_effect = Exception("Read error")
        
        with pytest.raises(InvalidFileFormatError) as exc_info:
            validate_file(file_path)
        assert "Read error" in str(exc_info.value)
    
    @patch('pdf_merger.utils.validators.get_file_columns')
    def test_custom_required_column(self, mock_get_columns, tmp_path):
        """Test validation with custom required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("custom_column,other\nvalue1,value2")
        mock_get_columns.return_value = ["custom_column", "other"]
        
        # Should not raise exception
        validate_file(file_path, required_column="custom_column")


class TestValidatePaths:
    """Test cases for validate_paths function."""
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_valid_all_paths(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when all paths are valid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = None  # No exception
        mock_validate_folder.return_value = None  # No exception
        
        # Should not raise exception
        validate_paths(file_path, source_folder, output_folder)
        
        mock_validate_file.assert_called_once_with(file_path, "serial_numbers")
        assert mock_validate_folder.call_count == 1
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_invalid_file(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when file is invalid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.side_effect = PDFMergerFileNotFoundError(file_path, file_type="Data file")
        
        with pytest.raises(PDFMergerFileNotFoundError):
            validate_paths(file_path, source_folder, output_folder)
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_invalid_source_folder(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when source folder is invalid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        mock_validate_file.return_value = None  # No exception
        mock_validate_folder.side_effect = PDFMergerFileNotFoundError(source_folder, file_type="Source folder")
        
        with pytest.raises(PDFMergerFileNotFoundError):
            validate_paths(file_path, source_folder, output_folder)
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_invalid_output_folder_parent(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when output folder parent doesn't exist."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "nonexistent" / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = None  # No exception
        mock_validate_folder.return_value = None  # No exception
        
        with pytest.raises(ValidationError) as exc_info:
            validate_paths(file_path, source_folder, output_folder)
        assert "output_folder" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_custom_required_column(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation with custom required column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = None  # No exception
        mock_validate_folder.return_value = None  # No exception
        
        # Should not raise exception
        validate_paths(
            file_path, source_folder, output_folder, required_column="custom_column"
        )
        
        mock_validate_file.assert_called_once_with(file_path, "custom_column")
