"""
Unit tests for validators module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.validators import (
    validate_serial_number,
    validate_folder,
    validate_file,
    validate_paths
)
from pdf_merger.exceptions import FileNotFoundError


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
        assert validate_folder(folder) is True
    
    def test_invalid_nonexistent_folder(self, tmp_path):
        """Test validation of non-existent folder."""
        folder = tmp_path / "nonexistent"
        assert validate_folder(folder) is False
    
    def test_invalid_file_not_folder(self, tmp_path):
        """Test validation when path is a file, not a folder."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test")
        assert validate_folder(file_path) is False
    
    def test_custom_folder_type(self, tmp_path):
        """Test validation with custom folder type."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        assert validate_folder(folder, "Source") is True


class TestValidateFile:
    """Test cases for validate_file function."""
    
    @patch('pdf_merger.validators.get_file_columns')
    def test_valid_file_with_required_column(self, mock_get_columns, tmp_path):
        """Test validation of file with required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("serial_numbers,other\nGRNW_001,value")
        mock_get_columns.return_value = ["serial_numbers", "other"]
        
        assert validate_file(file_path) is True
        mock_get_columns.assert_called_once_with(file_path)
    
    @patch('pdf_merger.validators.get_file_columns')
    def test_invalid_file_missing_column(self, mock_get_columns, tmp_path):
        """Test validation of file missing required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("other,value\nvalue1,value2")
        mock_get_columns.return_value = ["other", "value"]
        
        assert validate_file(file_path) is False
    
    @patch('pdf_merger.validators.get_file_columns')
    def test_invalid_nonexistent_file(self, mock_get_columns, tmp_path):
        """Test validation of non-existent file."""
        file_path = tmp_path / "nonexistent.csv"
        mock_get_columns.return_value = []
        
        assert validate_file(file_path) is False
        mock_get_columns.assert_not_called()
    
    @patch('pdf_merger.validators.get_file_columns')
    def test_invalid_file_read_error(self, mock_get_columns, tmp_path):
        """Test validation when file reading raises an error."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("test")
        mock_get_columns.side_effect = Exception("Read error")
        
        assert validate_file(file_path) is False
    
    @patch('pdf_merger.validators.get_file_columns')
    def test_custom_required_column(self, mock_get_columns, tmp_path):
        """Test validation with custom required column."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("custom_column,other\nvalue1,value2")
        mock_get_columns.return_value = ["custom_column", "other"]
        
        assert validate_file(file_path, required_column="custom_column") is True


class TestValidatePaths:
    """Test cases for validate_paths function."""
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_valid_all_paths(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when all paths are valid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = True
        mock_validate_folder.return_value = True
        
        is_valid, error_msg = validate_paths(file_path, source_folder, output_folder)
        
        assert is_valid is True
        assert error_msg == ""
        mock_validate_file.assert_called_once_with(file_path, "serial_numbers")
        assert mock_validate_folder.call_count == 1
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_invalid_file(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when file is invalid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = False
        
        is_valid, error_msg = validate_paths(file_path, source_folder, output_folder)
        
        assert is_valid is False
        assert error_msg == "File validation failed"
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_invalid_source_folder(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when source folder is invalid."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        mock_validate_file.return_value = True
        mock_validate_folder.return_value = False
        
        is_valid, error_msg = validate_paths(file_path, source_folder, output_folder)
        
        assert is_valid is False
        assert error_msg == "Source folder validation failed"
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_invalid_output_folder_parent(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation when output folder parent doesn't exist."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "nonexistent" / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = True
        mock_validate_folder.return_value = True
        
        is_valid, error_msg = validate_paths(file_path, source_folder, output_folder)
        
        assert is_valid is False
        assert error_msg == "Output folder parent validation failed"
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_custom_required_column(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test validation with custom required column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        mock_validate_file.return_value = True
        mock_validate_folder.return_value = True
        
        is_valid, error_msg = validate_paths(
            file_path, source_folder, output_folder, required_column="custom_column"
        )
        
        assert is_valid is True
        mock_validate_file.assert_called_once_with(file_path, "custom_column")
