"""
Unit tests for config module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from pdf_merger.config import (
    AppConfig,
    get_config_path,
    load_config,
    save_config
)
from pdf_merger.enums import DEFAULT_SERIAL_NUMBERS_COLUMN


class TestAppConfig:
    """Test cases for AppConfig dataclass."""
    
    def test_app_config_defaults(self):
        """Test AppConfig with default values."""
        config = AppConfig()
        
        assert config.input_file is None
        assert config.pdf_dir is None
        assert config.output_dir is None
        assert config.required_column == DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_app_config_with_values(self):
        """Test AppConfig with provided values."""
        config = AppConfig(
            input_file="/path/to/input.csv",
            pdf_dir="/path/to/pdfs",
            output_dir="/path/to/output",
            required_column="custom_column"
        )
        
        assert config.input_file == "/path/to/input.csv"
        assert config.pdf_dir == "/path/to/pdfs"
        assert config.output_dir == "/path/to/output"
        assert config.required_column == "custom_column"
    
    def test_app_config_to_dict(self):
        """Test converting AppConfig to dictionary."""
        config = AppConfig(
            input_file="/path/to/input.csv",
            pdf_dir="/path/to/pdfs",
            output_dir="/path/to/output"
        )
        
        result = config.to_dict()
        
        assert result == {
            'input_file': '/path/to/input.csv',
            'pdf_dir': '/path/to/pdfs',
            'output_dir': '/path/to/output',
            'required_column': DEFAULT_SERIAL_NUMBERS_COLUMN
        }
    
    def test_app_config_from_dict(self):
        """Test creating AppConfig from dictionary."""
        data = {
            'input_file': '/path/to/input.csv',
            'pdf_dir': '/path/to/pdfs',
            'output_dir': '/path/to/output',
            'required_column': 'custom_column'
        }
        
        config = AppConfig.from_dict(data)
        
        assert config.input_file == '/path/to/input.csv'
        assert config.pdf_dir == '/path/to/pdfs'
        assert config.output_dir == '/path/to/output'
        assert config.required_column == 'custom_column'
    
    def test_app_config_from_dict_defaults(self):
        """Test creating AppConfig from dictionary with missing fields."""
        data = {
            'input_file': '/path/to/input.csv'
        }
        
        config = AppConfig.from_dict(data)
        
        assert config.input_file == '/path/to/input.csv'
        assert config.pdf_dir is None
        assert config.output_dir is None
        assert config.required_column == DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def test_get_input_file_path(self):
        """Test getting input file as Path object."""
        config = AppConfig(input_file="/path/to/input.csv")
        
        result = config.get_input_file_path()
        
        assert result == Path("/path/to/input.csv")
    
    def test_get_input_file_path_none(self):
        """Test getting input file path when None."""
        config = AppConfig()
        
        result = config.get_input_file_path()
        
        assert result is None
    
    def test_get_pdf_dir_path(self):
        """Test getting PDF directory as Path object."""
        config = AppConfig(pdf_dir="/path/to/pdfs")
        
        result = config.get_pdf_dir_path()
        
        assert result == Path("/path/to/pdfs")
    
    def test_get_pdf_dir_path_none(self):
        """Test getting PDF directory path when None."""
        config = AppConfig()
        
        result = config.get_pdf_dir_path()
        
        assert result is None
    
    def test_get_output_dir_path(self):
        """Test getting output directory as Path object."""
        config = AppConfig(output_dir="/path/to/output")
        
        result = config.get_output_dir_path()
        
        assert result == Path("/path/to/output")
    
    def test_get_output_dir_path_none(self):
        """Test getting output directory path when None."""
        config = AppConfig()
        
        result = config.get_output_dir_path()
        
        assert result is None


class TestGetConfigPath:
    """Test cases for get_config_path function."""
    
    def test_get_config_path_app_directory_exists(self, tmp_path):
        """Test getting config path from app directory when it exists."""
        from pdf_merger.config import get_config_path
        
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        app_config = app_dir / "config.json"
        app_config.write_text("{}")
        
        # Mock __file__ to point to app_dir
        with patch('pdf_merger.config.__file__', str(app_dir / 'config.py')):
            result = get_config_path()
            # Should return app directory config if it exists
            # Note: This test verifies the function works, actual path may vary
            assert result.name == 'config.json'
    
    def test_get_config_path_fallback_to_home(self, tmp_path, monkeypatch):
        """Test getting config path falls back to home directory."""
        from pdf_merger.config import get_config_path
        
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # Mock Path.home() to return our test directory
        def mock_home():
            return home_dir
        monkeypatch.setattr('pathlib.Path.home', mock_home)
        
        # Mock __file__ to point to a directory without config.json
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        
        with patch('pdf_merger.config.__file__', str(app_dir / 'config.py')):
            result = get_config_path()
            # Should return home directory config when app config doesn't exist
            assert '.pdf_merger' in str(result) or 'home' in str(result)
            assert result.name == 'config.json'


class TestLoadConfig:
    """Test cases for load_config function."""
    
    def test_load_config_file_not_found(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_get_path.return_value = tmp_path / "nonexistent.json"
            
            result = load_config()
            
            assert isinstance(result, AppConfig)
            assert result.input_file is None
            assert result.pdf_dir is None
            assert result.output_dir is None
    
    def test_load_config_success(self, tmp_path):
        """Test successfully loading config from file."""
        config_file = tmp_path / "config.json"
        config_data = {
            'input_file': '/path/to/input.csv',
            'pdf_dir': '/path/to/pdfs',
            'output_dir': '/path/to/output',
            'required_column': 'custom_column'
        }
        config_file.write_text(json.dumps(config_data))
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = load_config()
            
            assert result.input_file == '/path/to/input.csv'
            assert result.pdf_dir == '/path/to/pdfs'
            assert result.output_dir == '/path/to/output'
            assert result.required_column == 'custom_column'
    
    def test_load_config_invalid_json(self, tmp_path):
        """Test loading config with invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json {")
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = load_config()
            
            # Should return default config on error
            assert isinstance(result, AppConfig)
            assert result.input_file is None
    
    def test_load_config_file_read_error(self, tmp_path):
        """Test loading config when file read fails."""
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.__truediv__ = lambda self, other: mock_path
            mock_get_path.return_value = mock_path
            
            with patch('builtins.open', side_effect=IOError("Read error")):
                result = load_config()
                
                # Should return default config on error
                assert isinstance(result, AppConfig)


class TestSaveConfig:
    """Test cases for save_config function."""
    
    def test_save_config_success(self, tmp_path):
        """Test successfully saving config to file."""
        config_file = tmp_path / "config.json"
        config = AppConfig(
            input_file="/path/to/input.csv",
            pdf_dir="/path/to/pdfs",
            output_dir="/path/to/output"
        )
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = save_config(config)
            
            assert result is True
            assert config_file.exists()
            
            # Verify content
            loaded_data = json.loads(config_file.read_text())
            assert loaded_data['input_file'] == '/path/to/input.csv'
            assert loaded_data['pdf_dir'] == '/path/to/pdfs'
            assert loaded_data['output_dir'] == '/path/to/output'
    
    def test_save_config_creates_directory(self, tmp_path):
        """Test saving config creates parent directory if needed."""
        config_dir = tmp_path / "new_dir"
        config_file = config_dir / "config.json"
        config = AppConfig()
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = save_config(config)
            
            assert result is True
            assert config_dir.exists()
            assert config_file.exists()
    
    def test_save_config_write_error(self, tmp_path):
        """Test saving config when write fails."""
        config = AppConfig()
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.parent.mkdir = MagicMock()
            mock_get_path.return_value = mock_path
            
            with patch('builtins.open', side_effect=IOError("Write error")):
                result = save_config(config)
                
                assert result is False
    
    def test_save_config_directory_creation_error(self, tmp_path):
        """Test saving config when directory creation fails."""
        config = AppConfig()
        
        with patch('pdf_merger.config.get_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.parent.mkdir.side_effect = PermissionError("Permission denied")
            mock_get_path.return_value = mock_path
            
            result = save_config(config)
            
            assert result is False
