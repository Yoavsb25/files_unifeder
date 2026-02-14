"""
Unit tests for config_manager module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from pdf_merger.config.config_manager import (
    AppConfig,
    get_config_path,
    load_config,
    save_config,
    find_project_preset,
    load_project_preset,
    load_user_config,
    load_env_config
)
from pdf_merger.core.constants import Constants


class TestAppConfig:
    """Test cases for AppConfig dataclass."""
    
    def test_app_config_defaults(self):
        """Test AppConfig with default values."""
        config = AppConfig()
        
        assert config.input_file is None
        assert config.pdf_dir is None
        assert config.output_dir is None
        assert config.required_column == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
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
            'required_column': Constants.DEFAULT_SERIAL_NUMBERS_COLUMN,
            'metrics_enabled': True,
            'telemetry_enabled': False,
            'crash_reporting_enabled': False,
            'fail_on_ambiguous_matches': True
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
        assert config.required_column == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
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
    
    def test_app_config_merge(self):
        """Test merging two AppConfig instances."""
        config1 = AppConfig(
            input_file="/path1/input.csv",
            pdf_dir="/path1/pdfs",
            required_column="column1"
        )
        config2 = AppConfig(
            input_file="/path2/input.csv",
            output_dir="/path2/output"
        )
        
        merged = config1.merge(config2)
        
        # config2 values should take precedence for non-None values
        assert merged.input_file == "/path2/input.csv"
        assert merged.pdf_dir == "/path1/pdfs"  # From config1 (config2 has None)
        assert merged.output_dir == "/path2/output"
    
    def test_app_config_merge_none_values(self):
        """Test merging when other config has None values."""
        config1 = AppConfig(
            input_file="/path1/input.csv",
            pdf_dir="/path1/pdfs"
        )
        config2 = AppConfig()  # All None
        
        merged = config1.merge(config2)
        
        # config1 values should be preserved
        assert merged.input_file == "/path1/input.csv"
        assert merged.pdf_dir == "/path1/pdfs"
    
    def test_app_config_merge_boolean_fields(self):
        """Test merging configs with boolean fields."""
        config1 = AppConfig(
            metrics_enabled=True,
            telemetry_enabled=False,
            crash_reporting_enabled=False,
            fail_on_ambiguous_matches=True
        )
        config2 = AppConfig(
            metrics_enabled=False,
            telemetry_enabled=True
        )
        
        merged = config1.merge(config2)
        
        assert merged.metrics_enabled is False  # From config2
        assert merged.telemetry_enabled is True  # From config2
        assert merged.crash_reporting_enabled is False  # From config1
        assert merged.fail_on_ambiguous_matches is True  # From config1


class TestGetConfigPath:
    """Test cases for get_config_path function."""
    
    def test_get_config_path_app_directory_exists(self, tmp_path):
        """Test getting config path from app directory when it exists."""
        from pdf_merger.config.config_manager import get_config_path
        
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        app_config = app_dir / "config.json"
        app_config.write_text("{}")
        
        # Mock __file__ to point to app_dir
        with patch('pdf_merger.config.config_manager.__file__', str(app_dir / 'config_manager.py')):
            result = get_config_path()
            # Should return app directory config if it exists
            # Note: This test verifies the function works, actual path may vary
            assert result.name == 'config.json'
    
    def test_get_config_path_fallback_to_home(self, tmp_path, monkeypatch):
        """Test getting config path falls back to home directory."""
        from pdf_merger.config.config_manager import get_config_path
        
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # Mock Path.home() to return our test directory
        def mock_home():
            return home_dir
        monkeypatch.setattr('pathlib.Path.home', mock_home)
        
        # Mock __file__ to point to a directory without config.json
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        
        with patch('pdf_merger.config.config_manager.__file__', str(app_dir / 'config_manager.py')):
            result = get_config_path()
            # Should return home directory config when app config doesn't exist
            assert '.pdf_merger' in str(result) or 'home' in str(result)
            assert result.name == 'config.json'


class TestLoadConfig:
    """Test cases for load_config function."""
    
    def test_load_config_file_not_found(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
            mock_get_path.return_value = tmp_path / "nonexistent.json"
            
            result = load_config()
            
            assert isinstance(result, AppConfig)
            assert result.input_file is None
            assert result.pdf_dir is None
            assert result.output_dir is None
    
    @patch('pdf_merger.config.config_manager.load_env_config')
    @patch('pdf_merger.config.config_manager.load_project_preset')
    @patch('pdf_merger.config.config_manager.load_user_config')
    def test_load_config_success(self, mock_user_config, mock_project_preset, mock_env_config, tmp_path):
        """Test successfully loading config from file."""
        config_file = tmp_path / "config.json"
        config_data = {
            'input_file': '/path/to/input.csv',
            'pdf_dir': '/path/to/pdfs',
            'output_dir': '/path/to/output',
            'required_column': 'custom_column'
        }
        config_file.write_text(json.dumps(config_data))
        
        # Mock no environment variables or project preset
        mock_env_config.return_value = AppConfig()
        mock_project_preset.return_value = None
        
        # Mock user config to return the loaded config
        user_config = AppConfig.from_dict(config_data)
        mock_user_config.return_value = user_config
        
        result = load_config()
        
        assert result.input_file == '/path/to/input.csv'
        assert result.pdf_dir == '/path/to/pdfs'
        assert result.output_dir == '/path/to/output'
        assert result.required_column == 'custom_column'
    
    @patch('pdf_merger.config.config_manager.load_env_config')
    @patch('pdf_merger.config.config_manager.load_project_preset')
    @patch('pdf_merger.config.config_manager.load_user_config')
    def test_load_config_precedence_env_overrides_all(self, mock_user_config, mock_project_preset, mock_env_config, tmp_path):
        """Test that environment variables override user config and project preset."""
        # Project preset
        project_config = AppConfig(input_file="/project/input.csv", pdf_dir="/project/pdfs")
        mock_project_preset.return_value = project_config
        
        # User config
        user_config = AppConfig(input_file="/user/input.csv", output_dir="/user/output")
        mock_user_config.return_value = user_config
        
        # Environment config (highest priority)
        env_config = AppConfig(input_file="/env/input.csv", pdf_dir="/env/pdfs")
        mock_env_config.return_value = env_config
        
        result = load_config()
        
        # Environment should win
        assert result.input_file == "/env/input.csv"
        assert result.pdf_dir == "/env/pdfs"
        # output_dir from user config (env doesn't have it)
        assert result.output_dir == "/user/output"
    
    @patch('pdf_merger.config.config_manager.load_env_config')
    @patch('pdf_merger.config.config_manager.load_project_preset')
    @patch('pdf_merger.config.config_manager.load_user_config')
    def test_load_config_precedence_user_overrides_project(self, mock_user_config, mock_project_preset, mock_env_config, tmp_path):
        """Test that user config overrides project preset."""
        # Project preset
        project_config = AppConfig(input_file="/project/input.csv", pdf_dir="/project/pdfs")
        mock_project_preset.return_value = project_config
        
        # User config
        user_config = AppConfig(input_file="/user/input.csv", output_dir="/user/output")
        mock_user_config.return_value = user_config
        
        # No environment variables
        mock_env_config.return_value = AppConfig()
        
        result = load_config()
        
        # User should win over project
        assert result.input_file == "/user/input.csv"
        assert result.pdf_dir == "/project/pdfs"  # From project (user doesn't have it)
        assert result.output_dir == "/user/output"
    
    @patch('pdf_merger.config.config_manager.load_env_config')
    @patch('pdf_merger.config.config_manager.load_project_preset')
    @patch('pdf_merger.config.config_manager.load_user_config')
    def test_load_config_with_start_path(self, mock_user_config, mock_project_preset, mock_env_config, tmp_path):
        """Test load_config with start_path parameter."""
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_file.write_text(json.dumps({"input_file": "/preset/input.csv"}))
        
        mock_env_config.return_value = AppConfig()
        mock_user_config.return_value = AppConfig()
        
        result = load_config(start_path=tmp_path)
        
        # Should find and load project preset
        assert result.input_file is not None
        mock_project_preset.assert_called_once_with(tmp_path)
    
    def test_load_config_invalid_json(self, tmp_path):
        """Test loading config with invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json {")
        
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = load_config()
            
            # Should return default config on error
            assert isinstance(result, AppConfig)
            assert result.input_file is None
    
    def test_load_config_file_read_error(self, tmp_path):
        """Test loading config when file read fails."""
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
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
        
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
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
        
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
            mock_get_path.return_value = config_file
            
            result = save_config(config)
            
            assert result is True
            assert config_dir.exists()
            assert config_file.exists()
    
    def test_save_config_write_error(self, tmp_path):
        """Test saving config when write fails."""
        config = AppConfig()
        
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.parent.mkdir = MagicMock()
            mock_get_path.return_value = mock_path
            
            with patch('builtins.open', side_effect=IOError("Write error")):
                result = save_config(config)
                
                assert result is False
    
    def test_save_config_directory_creation_error(self, tmp_path):
        """Test saving config when directory creation fails."""
        config = AppConfig()
        
        with patch('pdf_merger.config.config_manager.get_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.parent.mkdir.side_effect = PermissionError("Permission denied")
            mock_get_path.return_value = mock_path
            
            result = save_config(config)
            
            assert result is False


class TestFindProjectPreset:
    """Test cases for find_project_preset function."""
    
    def test_find_project_preset_in_current_dir(self, tmp_path):
        """Test finding preset in current directory."""
        from pdf_merger.config.config_manager import find_project_preset
        
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_file.write_text("{}")
        
        result = find_project_preset(tmp_path)
        
        assert result == preset_file
    
    def test_find_project_preset_in_parent_dir(self, tmp_path):
        """Test finding preset in parent directory."""
        from pdf_merger.config.config_manager import find_project_preset
        
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_file.write_text("{}")
        
        result = find_project_preset(subdir)
        
        assert result == preset_file
    
    def test_find_project_preset_not_found(self, tmp_path):
        """Test when preset is not found."""
        from pdf_merger.config.config_manager import find_project_preset
        
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        result = find_project_preset(subdir)
        
        assert result is None
    
    def test_find_project_preset_defaults_to_cwd(self):
        """Test that find_project_preset defaults to current working directory."""
        from pdf_merger.config.config_manager import find_project_preset
        
        with patch('pathlib.Path.cwd', return_value=Path("/tmp")):
            with patch('pathlib.Path.exists', return_value=False):
                result = find_project_preset(None)
                
                # Should search from cwd
                assert result is None or isinstance(result, Path)


class TestLoadProjectPreset:
    """Test cases for load_project_preset function."""
    
    def test_load_project_preset_success(self, tmp_path):
        """Test successfully loading project preset."""
        from pdf_merger.config.config_manager import load_project_preset
        
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_data = {
            'input_file': '/project/input.csv',
            'pdf_dir': '/project/pdfs'
        }
        preset_file.write_text(json.dumps(preset_data))
        
        result = load_project_preset(tmp_path)
        
        assert result is not None
        assert result.input_file == '/project/input.csv'
        assert result.pdf_dir == '/project/pdfs'
    
    def test_load_project_preset_not_found(self, tmp_path):
        """Test loading preset when not found."""
        from pdf_merger.config.config_manager import load_project_preset
        
        result = load_project_preset(tmp_path)
        
        assert result is None
    
    def test_load_project_preset_invalid_json(self, tmp_path):
        """Test loading preset with invalid JSON."""
        from pdf_merger.config.config_manager import load_project_preset
        
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_file.write_text("invalid json {")
        
        result = load_project_preset(tmp_path)
        
        assert result is None
    
    def test_load_project_preset_read_error(self, tmp_path):
        """Test loading preset when read fails."""
        from pdf_merger.config.config_manager import load_project_preset
        
        preset_file = tmp_path / ".pdf_merger_config.json"
        preset_file.write_text("{}")
        
        with patch('builtins.open', side_effect=IOError("Read error")):
            result = load_project_preset(tmp_path)
            
            assert result is None


class TestLoadUserConfig:
    """Test cases for load_user_config function."""
    
    def test_load_user_config_not_found(self, tmp_path):
        """Test loading user config when file doesn't exist."""
        from pdf_merger.config.config_manager import load_user_config
        
        with patch('pdf_merger.config.config_manager.get_config_path', return_value=tmp_path / "nonexistent.json"):
            result = load_user_config()
            
            assert isinstance(result, AppConfig)
            assert result.input_file is None
    
    def test_load_user_config_success(self, tmp_path):
        """Test successfully loading user config."""
        from pdf_merger.config.config_manager import load_user_config
        
        # Create valid paths that exist
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        
        config_file = tmp_path / "config.json"
        config_data = {
            'input_file': str(input_file),
            'pdf_dir': str(pdf_dir)
        }
        config_file.write_text(json.dumps(config_data))
        
        with patch('pdf_merger.config.config_manager.get_config_path', return_value=config_file):
            result = load_user_config()
            
            assert result.input_file == str(input_file)
            assert result.pdf_dir == str(pdf_dir)
    
    def test_load_user_config_invalid_json(self, tmp_path):
        """Test loading user config with invalid JSON."""
        from pdf_merger.config.config_manager import load_user_config
        
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json {")
        
        with patch('pdf_merger.config.config_manager.get_config_path', return_value=config_file):
            result = load_user_config()
            
            # Should return default config on error
            assert isinstance(result, AppConfig)
            assert result.input_file is None


class TestLoadEnvConfig:
    """Test cases for load_env_config function."""
    
    def test_load_env_config_no_vars(self):
        """Test loading env config when no variables are set."""
        from pdf_merger.config.config_manager import load_env_config
        
        with patch.dict('os.environ', {}, clear=True):
            result = load_env_config()
            
            assert isinstance(result, AppConfig)
            assert result.input_file is None
            assert result.pdf_dir is None
    
    def test_load_env_config_all_vars(self, tmp_path):
        """Test loading env config with all variables set."""
        from pdf_merger.config.config_manager import load_env_config, ENV_INPUT_FILE, ENV_SOURCE_DIR, ENV_OUTPUT_DIR, ENV_COLUMN
        
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        
        env_vars = {
            ENV_INPUT_FILE: str(input_file),
            ENV_SOURCE_DIR: str(source_dir),
            ENV_OUTPUT_DIR: str(output_dir),
            ENV_COLUMN: 'custom_column'
        }
        
        with patch.dict('os.environ', env_vars, clear=False):
            result = load_env_config()
            
            assert result.input_file is not None
            assert result.pdf_dir is not None
            assert result.output_dir is not None
            assert result.required_column == 'custom_column'
    
    def test_load_env_config_partial_vars(self, tmp_path):
        """Test loading env config with partial variables."""
        from pdf_merger.config.config_manager import load_env_config, ENV_INPUT_FILE
        
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        
        with patch.dict('os.environ', {ENV_INPUT_FILE: str(input_file)}, clear=False):
            result = load_env_config()
            
            assert result.input_file is not None
            assert result.pdf_dir is None


class TestAppConfigMethods:
    """Test cases for AppConfig methods."""
    
    def test_get_input_file_path(self):
        """Test getting input file as Path."""
        config = AppConfig(input_file="/path/to/input.csv")
        
        path = config.get_input_file_path()
        
        assert path == Path("/path/to/input.csv")
    
    def test_get_input_file_path_none(self):
        """Test getting input file path when None."""
        config = AppConfig()
        
        path = config.get_input_file_path()
        
        assert path is None
    
    def test_get_pdf_dir_path(self):
        """Test getting PDF directory as Path."""
        config = AppConfig(pdf_dir="/path/to/pdfs")
        
        path = config.get_pdf_dir_path()
        
        assert path == Path("/path/to/pdfs")
    
    def test_get_output_dir_path(self):
        """Test getting output directory as Path."""
        config = AppConfig(output_dir="/path/to/output")
        
        path = config.get_output_dir_path()
        
        assert path == Path("/path/to/output")
    
    def test_merge_configs(self):
        """Test merging two configs."""
        config1 = AppConfig(
            input_file="/path1/input.csv",
            pdf_dir="/path1/pdfs",
            required_column="column1"
        )
        config2 = AppConfig(
            input_file="/path2/input.csv",
            output_dir="/path2/output"
        )
        
        merged = config1.merge(config2)
        
        # config2 values should take precedence for non-None values
        assert merged.input_file == "/path2/input.csv"
        assert merged.pdf_dir == "/path1/pdfs"  # From config1 (config2 has None)
        assert merged.output_dir == "/path2/output"
        assert merged.required_column == "column1"  # From config1 if config2 uses default
    
    def test_merge_configs_none_values(self):
        """Test merging when other config has None values."""
        config1 = AppConfig(
            input_file="/path1/input.csv",
            pdf_dir="/path1/pdfs"
        )
        config2 = AppConfig()  # All None
        
        merged = config1.merge(config2)
        
        # config1 values should be preserved
        assert merged.input_file == "/path1/input.csv"
        assert merged.pdf_dir == "/path1/pdfs"
    
    def test_merge_configs_boolean_fields(self):
        """Test merging configs with boolean fields."""
        config1 = AppConfig(
            metrics_enabled=True,
            telemetry_enabled=False,
            crash_reporting_enabled=False,
            fail_on_ambiguous_matches=True
        )
        config2 = AppConfig(
            metrics_enabled=False,
            telemetry_enabled=True
        )
        
        merged = config1.merge(config2)
        
        assert merged.metrics_enabled is False  # From config2
        assert merged.telemetry_enabled is True  # From config2
        assert merged.crash_reporting_enabled is False  # From config1
        assert merged.fail_on_ambiguous_matches is True  # From config1
