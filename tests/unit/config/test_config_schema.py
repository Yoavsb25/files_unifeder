"""
Unit tests for config_schema module.
"""

import pytest
from pathlib import Path
from pdf_merger.config.config_schema import ConfigSchema
from pdf_merger.core.constants import Constants


class TestConfigSchema:
    """Test cases for ConfigSchema class."""
    
    def test_validate_input_file_valid(self, tmp_path):
        """Test validating a valid input file."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("test")
        
        result = ConfigSchema.validate_input_file(str(test_file))
        
        assert result is not None
        assert Path(result).exists()
        assert Path(result).is_file()
    
    def test_validate_input_file_none(self):
        """Test validating None input file."""
        result = ConfigSchema.validate_input_file(None)
        
        assert result is None
    
    def test_validate_input_file_empty_string(self):
        """Test validating empty string input file."""
        result = ConfigSchema.validate_input_file("")
        
        assert result is None
    
    def test_validate_input_file_not_exists(self):
        """Test validating non-existent input file."""
        with pytest.raises(ValueError, match="does not exist"):
            ConfigSchema.validate_input_file("/nonexistent/file.csv")
    
    def test_validate_input_file_not_file(self, tmp_path):
        """Test validating input file that is a directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        with pytest.raises(ValueError, match="is not a file"):
            ConfigSchema.validate_input_file(str(test_dir))
    
    def test_validate_source_dir_valid(self, tmp_path):
        """Test validating a valid source directory."""
        test_dir = tmp_path / "source"
        test_dir.mkdir()
        
        result = ConfigSchema.validate_source_dir(str(test_dir))
        
        assert result is not None
        assert Path(result).exists()
        assert Path(result).is_dir()
    
    def test_validate_source_dir_none(self):
        """Test validating None source directory."""
        result = ConfigSchema.validate_source_dir(None)
        
        assert result is None
    
    def test_validate_source_dir_empty_string(self):
        """Test validating empty string source directory."""
        result = ConfigSchema.validate_source_dir("")
        
        assert result is None
    
    def test_validate_source_dir_not_exists(self):
        """Test validating non-existent source directory."""
        with pytest.raises(ValueError, match="does not exist"):
            ConfigSchema.validate_source_dir("/nonexistent/dir")
    
    def test_validate_source_dir_not_dir(self, tmp_path):
        """Test validating source directory that is a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError, match="is not a directory"):
            ConfigSchema.validate_source_dir(str(test_file))
    
    def test_validate_output_dir_valid_existing(self, tmp_path):
        """Test validating an existing output directory."""
        test_dir = tmp_path / "output"
        test_dir.mkdir()
        
        result = ConfigSchema.validate_output_dir(str(test_dir))
        
        assert result is not None
        assert Path(result).exists()
        assert Path(result).is_dir()
    
    def test_validate_output_dir_valid_new(self, tmp_path):
        """Test validating a new output directory (will be created)."""
        test_dir = tmp_path / "new_output"
        
        result = ConfigSchema.validate_output_dir(str(test_dir))
        
        assert result is not None
        # Parent should exist (created by validation)
        assert test_dir.parent.exists()
    
    def test_validate_output_dir_none(self):
        """Test validating None output directory."""
        result = ConfigSchema.validate_output_dir(None)
        
        assert result is None
    
    def test_validate_output_dir_empty_string(self):
        """Test validating empty string output directory."""
        result = ConfigSchema.validate_output_dir("")
        
        assert result is None
    
    def test_validate_output_dir_exists_but_not_dir(self, tmp_path):
        """Test validating output directory when path exists but is a file."""
        test_file = tmp_path / "output.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError, match="exists but is not a directory"):
            ConfigSchema.validate_output_dir(str(test_file))
    
    def test_validate_column_valid(self):
        """Test validating a valid column name."""
        result = ConfigSchema.validate_column("custom_column")
        
        assert result == "custom_column"
    
    def test_validate_column_none(self):
        """Test validating None column name (should return default)."""
        result = ConfigSchema.validate_column(None)
        
        assert result == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_validate_column_empty_string(self):
        """Test validating empty string column name (should return default)."""
        result = ConfigSchema.validate_column("")
        
        assert result == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_validate_column_whitespace_only(self):
        """Test validating whitespace-only column name."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            ConfigSchema.validate_column("   ")
    
    def test_validate_column_strips_whitespace(self):
        """Test that column name whitespace is stripped."""
        result = ConfigSchema.validate_column("  custom_column  ")
        
        assert result == "custom_column"
    
    def test_validate_column_invalid_type(self):
        """Test validating invalid column type."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            ConfigSchema.validate_column(123)
    
    def test_validate_config_complete(self, tmp_path):
        """Test validating a complete configuration."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        
        config = {
            'input_file': str(input_file),
            'pdf_dir': str(source_dir),
            'output_dir': str(output_dir),
            'required_column': 'custom_column'
        }
        
        result = ConfigSchema.validate_config(config)
        
        assert result['input_file'] is not None
        assert result['pdf_dir'] is not None
        assert result['output_dir'] is not None
        assert result['required_column'] == 'custom_column'
    
    def test_validate_config_minimal(self):
        """Test validating minimal configuration."""
        config = {}
        
        result = ConfigSchema.validate_config(config)
        
        assert 'input_file' not in result or result['input_file'] is None
        assert 'pdf_dir' not in result or result['pdf_dir'] is None
        assert 'output_dir' not in result or result['output_dir'] is None
        assert result['required_column'] == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_validate_config_invalid_input_file(self, tmp_path):
        """Test validating config with invalid input file."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        config = {
            'input_file': '/nonexistent/file.csv',
            'pdf_dir': str(source_dir)
        }
        
        result = ConfigSchema.validate_config(config)
        
        # Invalid input_file should be set to None with warning logged
        assert result['input_file'] is None
    
    def test_validate_config_invalid_source_dir(self, tmp_path):
        """Test validating config with invalid source directory."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        
        config = {
            'input_file': str(input_file),
            'pdf_dir': '/nonexistent/dir'
        }
        
        result = ConfigSchema.validate_config(config)
        
        # Invalid pdf_dir should be set to None with warning logged
        assert result['pdf_dir'] is None
    
    def test_validate_config_source_dir_alias(self, tmp_path):
        """Test validating config with source_dir alias."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        config = {
            'source_dir': str(source_dir)
        }
        
        result = ConfigSchema.validate_config(config)
        
        # source_dir should be mapped to pdf_dir
        assert result['pdf_dir'] is not None
        assert result['pdf_dir'] == str(source_dir.resolve())
    
    def test_validate_config_source_dir_precedence(self, tmp_path):
        """Test that pdf_dir takes precedence over source_dir."""
        pdf_dir = tmp_path / "pdfs"
        source_dir = tmp_path / "source"
        pdf_dir.mkdir()
        source_dir.mkdir()
        
        config = {
            'pdf_dir': str(pdf_dir),
            'source_dir': str(source_dir)
        }
        
        result = ConfigSchema.validate_config(config)
        
        # pdf_dir should be used, not source_dir
        assert result['pdf_dir'] == str(pdf_dir.resolve())
    
    def test_validate_config_invalid_column(self, tmp_path):
        """Test validating config with invalid column name."""
        config = {
            'required_column': '   '  # Whitespace only
        }
        
        result = ConfigSchema.validate_config(config)
        
        # Invalid column should default to Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
        assert result['required_column'] == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_validate_config_no_column(self):
        """Test validating config without column (should use default)."""
        config = {}
        
        result = ConfigSchema.validate_config(config)
        
        assert result['required_column'] == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
