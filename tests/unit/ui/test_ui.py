"""
Unit tests for UI module.
"""

import pytest
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, call, Mock

# Mock tkinter before importing UI module
import sys

# Create a proper mock class for CTk that can be used in issubclass checks
class MockCTk(object):
    """Mock CTk class that can be used in isinstance/issubclass checks."""
    def __init__(self, *args, **kwargs):
        pass
    def title(self, *args, **kwargs):
        pass
    def geometry(self, *args, **kwargs):
        pass
    def minsize(self, *args, **kwargs):
        pass
    def mainloop(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass

class MockCTkFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass

class MockCTkLabel:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass

class MockCTkButton:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass

class MockCTkTextbox:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def insert(self, *args, **kwargs):
        pass
    def see(self, *args, **kwargs):
        pass
    def delete(self, *args, **kwargs):
        pass

class MockCTkFont:
    def __init__(self, *args, **kwargs):
        pass
    @staticmethod
    def __call__(*args, **kwargs):
        return MagicMock()

# Mock the modules
mock_tkinter = MagicMock()
mock_tkinter.filedialog = MagicMock()
sys.modules['tkinter'] = mock_tkinter
sys.modules['tkinter.filedialog'] = mock_tkinter.filedialog

# Create mock_ctk module with proper class references
from types import ModuleType
mock_ctk = ModuleType('customtkinter')
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkFrame
mock_ctk.CTkLabel = MockCTkLabel
mock_ctk.CTkButton = MockCTkButton
mock_ctk.CTkTextbox = MockCTkTextbox
mock_ctk.CTkFont = MockCTkFont
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
sys.modules['customtkinter'] = mock_ctk

from pdf_merger.ui.app import PDFMergerApp, run_gui
from pdf_merger.ui.components import LogHandler
from pdf_merger.enums import StatusColor
from pdf_merger.licensing import LicenseStatus
from pdf_merger.processor import ProcessingResult


class TestPDFMergerApp:
    """Test cases for PDFMergerApp class."""
    
    def _create_mock_app(self):
        """Helper to create a mock PDFMergerApp instance."""
        # Create app instance without calling __init__
        # Use object.__new__ to bypass CTk.__init__
        app = object.__new__(PDFMergerApp)
        # Set up required attributes manually
        app.license_manager = MagicMock()
        app.license_valid = False
        app.input_file_path = None
        app.pdf_dir_path = None
        app.output_dir_path = None
        app.config = MagicMock()
        app.run_button = MagicMock()
        
        # Mock components
        app.license_frame = MagicMock()
        app.license_frame.license_label = MagicMock()
        app.log_area = MagicMock()
        app.log_area.log_text = MagicMock()
        app.footer = MagicMock()
        app.footer.status_label = MagicMock()
        
        # Mock file selectors
        app.input_file_selector = MagicMock()
        app.pdf_dir_selector = MagicMock()
        app.output_dir_selector = MagicMock()
        
        # Mock handlers
        app.file_handler = MagicMock()
        app.merge_handler = MagicMock()
        app.merge_handler.is_processing = False
        
        return app
    
    @patch('pdf_merger.ui.app.LicenseManager')
    def test_app_initialization(self, mock_license_manager):
        """Test app initialization."""
        mock_manager = MagicMock()
        mock_manager.get_license_status.return_value = LicenseStatus.VALID
        mock_manager.get_license_info.return_value = {
            'company': 'Test',
            'expires': '2027-12-31'
        }
        mock_license_manager.return_value = mock_manager
        
        app = self._create_mock_app()
        
        assert app.license_manager is not None
        assert app.input_file_path is None
        assert app.pdf_dir_path is None
        assert app.output_dir_path is None
        assert app.merge_handler.is_processing is False
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_valid(self, mock_update_license):
        """Test checking valid license."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        app._check_license()
        
        assert app.license_valid is True
        mock_update_license.assert_called_once_with(
            app.license_manager,
            app.license_frame.license_label
        )
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_expired(self, mock_update_license):
        """Test checking expired license."""
        mock_update_license.return_value = False
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        app._check_license()
        
        assert app.license_valid is False
    
    def test_select_input_file_success(self):
        """Test selecting input file successfully."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        mock_path = Path("/path/to/input.csv")
        app.file_handler.select_input_file.return_value = mock_path
        
        app._select_input_file()
        
        assert app.input_file_path == mock_path
        app.input_file_selector.set_path.assert_called_once_with(str(mock_path))
        app._update_ui_state.assert_called_once()
    
    def test_select_input_file_cancelled(self):
        """Test cancelling input file selection."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app.file_handler.select_input_file.return_value = None
        
        app._select_input_file()
        
        assert app.input_file_path is None
        app.input_file_selector.set_path.assert_not_called()
    
    def test_select_pdf_directory_success(self):
        """Test selecting PDF directory successfully."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        mock_path = Path("/path/to/pdfs")
        app.file_handler.select_directory.return_value = mock_path
        
        app._select_pdf_directory()
        
        assert app.pdf_dir_path == mock_path
        app.pdf_dir_selector.set_path.assert_called_once_with(str(mock_path))
        app._update_ui_state.assert_called_once()
    
    def test_select_output_directory_success(self, tmp_path):
        """Test selecting output directory successfully."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        output_dir = tmp_path / "output"
        app.file_handler.select_directory.return_value = output_dir
        
        app._select_output_directory()
        
        assert app.output_dir_path == output_dir
        app.output_dir_selector.set_path.assert_called_once_with(str(output_dir))
        app._update_ui_state.assert_called_once()
    
    def test_select_output_directory_cancelled(self):
        """Test cancelling output directory selection."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app.file_handler.select_directory.return_value = None
        
        app._select_output_directory()
        
        assert app.output_dir_path is None
        app.output_dir_selector.set_path.assert_not_called()
    
    @patch('pdf_merger.ui.app.logger')
    def test_log(self, mock_logger):
        """Test logging to log area."""
        app = self._create_mock_app()
        
        app._log("Test message")
        
        app.log_area.log.assert_called_once_with("Test message")
        mock_logger.info.assert_called_once_with("Test message")
    
    def test_show_error(self):
        """Test showing error message."""
        app = self._create_mock_app()
        app._log = MagicMock()
        
        app._show_error("Error message")
        
        app._log.assert_called_once_with("ERROR: Error message")
        app.footer.update_status.assert_called_once_with("Error", StatusColor.RED)
    
    def test_run_merge_success(self, tmp_path):
        """Test running merge operation successfully."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = tmp_path / "input.csv"
        app.pdf_dir_path = tmp_path / "pdfs"
        app.output_dir_path = tmp_path / "output"
        
        app._run_merge()
        
        app.merge_handler.run_merge.assert_called_once_with(
            input_file=app.input_file_path,
            pdf_dir=app.pdf_dir_path,
            output_dir=app.output_dir_path
        )
    
    def test_run_merge_invalid_license(self):
        """Test running merge with invalid license."""
        app = self._create_mock_app()
        app.license_valid = False
        app._show_error = MagicMock()
        
        app._run_merge()
        
        app._show_error.assert_called_once()
    
    def test_run_merge_missing_paths(self):
        """Test running merge with missing paths."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = None
        app._show_error = MagicMock()
        
        app._run_merge()
        
        app._show_error.assert_called_once()
    
    def test_run_merge_already_processing(self):
        """Test running merge when already processing."""
        app = self._create_mock_app()
        app.license_valid = True
        app.merge_handler.is_processing = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        
        app._run_merge()
        
        # Handler should check is_processing internally
        app.merge_handler.run_merge.assert_called_once()
    
    def test_on_merge_start(self):
        """Test merge start handler."""
        app = self._create_mock_app()
        app._log = MagicMock()
        
        app._on_merge_start()
        
        app.run_button.configure.assert_called_with(state="disabled", text="Processing...")
        app.footer.update_status.assert_called_with("Processing...", StatusColor.BLUE)
        app.log_area.clear.assert_called_once()
        assert app._log.call_count >= 4  # Multiple log calls
    
    def test_on_merge_complete_success(self):
        """Test merge completion handler with full success."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app.merge_handler.format_result = MagicMock(return_value="Summary text")
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=5,
            failed_rows=[]
        )
        
        app._on_merge_complete(result)
        
        assert app.merge_handler.is_processing is False
        app.run_button.configure.assert_called_with(state="normal", text="Run Merge")
        app.footer.update_status.assert_called_with("Success", StatusColor.GREEN)
        app.merge_handler.format_result.assert_called_once_with(result)
    
    def test_on_merge_error(self):
        """Test merge error handler."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._on_merge_error("Error message")
        
        assert app.merge_handler.is_processing is False
        app.run_button.configure.assert_called_with(state="normal", text="Run Merge")
        app.footer.update_status.assert_called_with("Error", StatusColor.RED)
        assert app._log.call_count >= 2  # Multiple log calls
    
    def test_update_ui_state_all_selected(self):
        """Test updating UI state when all paths are selected."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.merge_handler.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="normal")
    
    def test_update_ui_state_missing_paths(self):
        """Test updating UI state when paths are missing."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = None
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.merge_handler.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")
    
    def test_update_ui_state_processing(self):
        """Test updating UI state when processing."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.merge_handler.is_processing = True
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")
    
    def test_update_ui_state_invalid_license(self):
        """Test updating UI state with invalid license."""
        app = self._create_mock_app()
        app.license_valid = False
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.merge_handler.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")
    
    @patch('pdf_merger.validators.validate_file')
    @patch('pdf_merger.validators.validate_folder')
    def test_load_config_into_ui_all_fields(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test loading config into UI with all fields."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        
        from pdf_merger.config import AppConfig
        mock_config = AppConfig(
            input_file=str(input_file),
            pdf_dir=str(source_dir),
            output_dir=str(output_dir)
        )
        
        app = self._create_mock_app()
        app.config = mock_config
        app._update_ui_state = MagicMock()
        
        app._load_config_into_ui()
        
        assert app.input_file_path == input_file
        assert app.pdf_dir_path == source_dir
        assert app.output_dir_path == output_dir
        app._update_ui_state.assert_called()
    
    def test_load_config_into_ui_invalid_input_file(self, tmp_path):
        """Test loading config with invalid input file."""
        from pdf_merger.config import AppConfig
        mock_config = AppConfig(
            input_file="/nonexistent/file.csv"
        )
        
        app = self._create_mock_app()
        app.config = mock_config
        app._update_ui_state = MagicMock()
        
        app._load_config_into_ui()
        
        # Invalid file should not be loaded
        assert app.input_file_path is None
    
    def test_load_config_into_ui_invalid_source_dir(self):
        """Test loading config with invalid source directory."""
        from pdf_merger.config import AppConfig
        mock_config = AppConfig(
            pdf_dir="/nonexistent/dir"
        )
        
        app = self._create_mock_app()
        app.config = mock_config
        app._update_ui_state = MagicMock()
        
        app._load_config_into_ui()
        
        # Invalid directory should not be loaded
        assert app.pdf_dir_path is None
    
    def test_load_config_into_ui_output_dir_creation(self, tmp_path):
        """Test loading config with output directory that gets created."""
        output_dir = tmp_path / "new_output"
        
        from pdf_merger.config import AppConfig
        mock_config = AppConfig(
            output_dir=str(output_dir)
        )
        
        app = self._create_mock_app()
        app.config = mock_config
        app._update_ui_state = MagicMock()
        
        app._load_config_into_ui()
        
        # Output directory should be created and loaded
        assert app.output_dir_path == output_dir
        assert output_dir.exists()
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_with_warning_critical(self, mock_update_license):
        """Test checking license with critical expiry warning."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is True
        mock_update_license.assert_called_once()
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_with_warning_warning(self, mock_update_license):
        """Test checking license with warning level expiry."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is True
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_with_warning_info(self, mock_update_license):
        """Test checking license with info level expiry."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is True
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_without_warning(self, mock_update_license):
        """Test checking license without expiry warning."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is True
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_no_info(self, mock_update_license):
        """Test checking license when get_license_info returns None."""
        mock_update_license.return_value = True
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is True
    
    @patch('pdf_merger.ui.app.update_license_display')
    def test_check_license_invalid_status(self, mock_update_license):
        """Test checking license with invalid status."""
        mock_update_license.return_value = False
        
        app = self._create_mock_app()
        app._update_ui_state = MagicMock()
        
        app._check_license()
        
        assert app.license_valid is False
    
    def test_on_merge_complete_partial_success(self):
        """Test merge completion with partial success."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app.merge_handler.format_result = MagicMock(return_value="Summary text")
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=3,
            failed_rows=[2, 4]
        )
        
        app._on_merge_complete(result)
        
        assert app.merge_handler.is_processing is False
        app.footer.update_status.assert_called_with("Partial success", StatusColor.ORANGE)
    
    def test_on_merge_complete_failed(self):
        """Test merge completion with all failures."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app.merge_handler.format_result = MagicMock(return_value="Summary text")
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=0,
            failed_rows=[1, 2, 3, 4, 5]
        )
        
        app._on_merge_complete(result)
        
        assert app.merge_handler.is_processing is False
        app.footer.update_status.assert_called_with("Failed", StatusColor.RED)


class TestRunGui:
    """Test cases for run_gui function."""
    
    @patch('pdf_merger.ui.app.PDFMergerApp')
    def test_run_gui(self, mock_app_class):
        """Test running GUI application."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app
        
        run_gui()
        
        mock_app_class.assert_called_once()
        mock_app.mainloop.assert_called_once()
