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

from pdf_merger.ui.app import PDFMergerApp, LogHandler, run_gui
from pdf_merger.licensing import LicenseStatus
from pdf_merger.processor import ProcessingResult


class TestLogHandler:
    """Test cases for LogHandler class."""
    
    def test_log_handler_write(self):
        """Test writing to log handler."""
        mock_widget = MagicMock()
        handler = LogHandler(mock_widget)
        
        handler.write("Test message")
        handler.write("Another message")
        
        assert len(handler.buffer) == 2
        assert "Test message" in handler.buffer
        assert "Another message" in handler.buffer
    
    def test_log_handler_write_empty(self):
        """Test writing empty message to log handler."""
        mock_widget = MagicMock()
        handler = LogHandler(mock_widget)
        
        handler.write("")
        handler.write("   ")
        
        assert len(handler.buffer) == 0
    
    def test_log_handler_flush(self):
        """Test flushing log handler buffer."""
        mock_widget = MagicMock()
        handler = LogHandler(mock_widget)
        
        handler.write("Message 1")
        handler.write("Message 2")
        handler.flush()
        
        mock_widget.insert.assert_called_once()
        mock_widget.see.assert_called_once_with("end")
        assert len(handler.buffer) == 0
    
    def test_log_handler_flush_empty(self):
        """Test flushing empty buffer."""
        mock_widget = MagicMock()
        handler = LogHandler(mock_widget)
        
        handler.flush()
        
        mock_widget.insert.assert_not_called()


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
        app.is_processing = False
        app.run_button = MagicMock()
        app.status_label = MagicMock()
        app.log_text = MagicMock()
        app.input_file_label = MagicMock()
        app.pdf_dir_label = MagicMock()
        app.output_dir_label = MagicMock()
        app.license_label = MagicMock()
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
        assert app.is_processing is False
    
    @patch('pdf_merger.ui.app.LicenseManager')
    def test_check_license_valid(self, mock_license_manager):
        """Test checking valid license."""
        mock_manager = MagicMock()
        mock_manager.get_license_status.return_value = LicenseStatus.VALID
        mock_manager.get_license_info.return_value = {
            'company': 'Test Company',
            'expires': '2027-12-31'
        }
        mock_license_manager.return_value = mock_manager
        
        app = self._create_mock_app()
        app.license_manager = mock_manager
        app._check_license()
        
        assert app.license_valid is True
        mock_manager.get_license_status.assert_called_once()
    
    @patch('pdf_merger.ui.app.LicenseManager')
    def test_check_license_expired(self, mock_license_manager):
        """Test checking expired license."""
        mock_manager = MagicMock()
        mock_manager.get_license_status.return_value = LicenseStatus.EXPIRED
        mock_manager.get_license_error_message.return_value = "License expired"
        mock_license_manager.return_value = mock_manager
        
        app = self._create_mock_app()
        app.license_manager = mock_manager
        app._check_license()
        
        assert app.license_valid is False
    
    @patch('pdf_merger.ui.app.filedialog.askopenfilename')
    @patch('pdf_merger.ui.app.validate_file')
    def test_select_input_file_success(self, mock_validate, mock_dialog):
        """Test selecting input file successfully."""
        mock_validate.return_value = None  # No exception raised
        mock_dialog.return_value = "/path/to/input.csv"
        
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._select_input_file()
        
        assert app.input_file_path == Path("/path/to/input.csv")
        app.input_file_label.configure.assert_called_once()
        app._update_ui_state.assert_called_once()
    
    @patch('pdf_merger.ui.app.filedialog.askopenfilename')
    @patch('pdf_merger.ui.app.validate_file')
    def test_select_input_file_invalid(self, mock_validate, mock_dialog):
        """Test selecting invalid input file."""
        from pdf_merger.exceptions import FileNotFoundError
        mock_validate.side_effect = FileNotFoundError(Path("/path/to/invalid.txt"), file_type="Data file")
        mock_dialog.return_value = "/path/to/invalid.txt"
        
        app = self._create_mock_app()
        app._log = MagicMock()
        app._show_error = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._select_input_file()
        
        assert app.input_file_path is None
        app._show_error.assert_called_once()
    
    @patch('pdf_merger.ui.app.filedialog.askdirectory')
    @patch('pdf_merger.ui.app.validate_folder')
    def test_select_pdf_directory_success(self, mock_validate, mock_dialog):
        """Test selecting PDF directory successfully."""
        mock_validate.return_value = None  # No exception raised
        mock_dialog.return_value = "/path/to/pdfs"
        
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._select_pdf_directory()
        
        assert app.pdf_dir_path == Path("/path/to/pdfs")
        app.pdf_dir_label.configure.assert_called_once()
        app._update_ui_state.assert_called_once()
    
    @patch('pdf_merger.ui.app.filedialog.askdirectory')
    @patch('pdf_merger.ui.app.validate_folder')
    def test_select_output_directory_success(self, mock_validate, mock_dialog, tmp_path):
        """Test selecting output directory successfully."""
        mock_validate.return_value = None  # No exception raised
        output_dir = tmp_path / "output"
        mock_dialog.return_value = str(output_dir)
        
        app = self._create_mock_app()
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._select_output_directory()
        
        assert app.output_dir_path == output_dir
        app.output_dir_label.configure.assert_called_once()
        app._update_ui_state.assert_called_once()
    
    @patch('pdf_merger.ui.app.filedialog.askdirectory')
    def test_select_output_directory_creation_error(self, mock_dialog, tmp_path):
        """Test selecting output directory when creation fails."""
        output_dir = tmp_path / "output"
        mock_dialog.return_value = str(output_dir)
        
        app = self._create_mock_app()
        app._log = MagicMock()
        app._show_error = MagicMock()
        app._update_ui_state = MagicMock()
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            app._select_output_directory()
            
            app._show_error.assert_called_once()
    
    def test_log(self):
        """Test logging to text widget."""
        app = self._create_mock_app()
        
        app._log("Test message")
        
        app.log_text.insert.assert_called_once_with("end", "Test message\n")
        app.log_text.see.assert_called_once_with("end")
    
    def test_show_error(self):
        """Test showing error message."""
        app = self._create_mock_app()
        app._log = MagicMock()
        
        app._show_error("Error message")
        
        app._log.assert_called_once_with("ERROR: Error message")
        app.status_label.configure.assert_called_once()
    
    @patch('pdf_merger.ui.app.run_merge')
    @patch('pdf_merger.ui.app.threading.Thread')
    def test_run_merge_success(self, mock_thread, mock_run_merge, tmp_path):
        """Test running merge operation successfully."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = tmp_path / "input.csv"
        app.pdf_dir_path = tmp_path / "pdfs"
        app.output_dir_path = tmp_path / "output"
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=5,
            failed_rows=[]
        )
        mock_run_merge.return_value = result
        
        # Mock after() to execute callback immediately
        callback_executed = False
        def after_side_effect(delay, callback, *args):
            nonlocal callback_executed
            # Execute callback immediately in test (simulating main thread callback)
            # The callback is _merge_complete and args contains the result
            callback(*args)
            callback_executed = True
        
        app.after = MagicMock(side_effect=after_side_effect)
        
        # Mock the thread to call the worker immediately
        def thread_side_effect(*args, **kwargs):
            thread = MagicMock()
            def start_thread():
                # Execute worker which will call app.after()
                app._merge_worker()
            thread.start = start_thread
            return thread
        mock_thread.side_effect = thread_side_effect
        
        app._run_merge()
        
        # Execute the thread start to trigger the worker
        if mock_thread.called:
            thread_instance = mock_thread.return_value
            thread_instance.start()
        
        # Verify callback was executed
        assert callback_executed, "Callback should have been executed"
        assert app.after.called, "app.after() should have been called"
        
        # Verify UI was updated - is_processing should be False after callback
        app.run_button.configure.assert_called()
        # The callback should have been called, resetting is_processing
        assert app.is_processing is False, f"Expected is_processing to be False, but it's {app.is_processing}"
    
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
        app.is_processing = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        
        app._run_merge()
        
        # Should not start another merge
        assert app.is_processing is True
    
    @patch('pdf_merger.ui.app.run_merge')
    def test_merge_worker_success(self, mock_run_merge):
        """Test merge worker thread success."""
        app = self._create_mock_app()
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.after = MagicMock()
        
        result = ProcessingResult(
            total_rows=3,
            successful_merges=3,
            failed_rows=[]
        )
        mock_run_merge.return_value = result
        
        app._merge_worker()
        
        # Verify after() was called to update UI
        app.after.assert_called_once()
        call_args = app.after.call_args[0]
        assert call_args[0] == 0
        assert call_args[1] == app._merge_complete
    
    @patch('pdf_merger.ui.app.run_merge')
    def test_merge_worker_error(self, mock_run_merge):
        """Test merge worker thread error."""
        app = self._create_mock_app()
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.after = MagicMock()
        
        mock_run_merge.side_effect = ValueError("Processing error")
        
        app._merge_worker()
        
        # Verify after() was called with error handler
        app.after.assert_called_once()
        call_args = app.after.call_args[0]
        assert call_args[0] == 0
        assert call_args[1] == app._merge_error
    
    @patch('pdf_merger.ui.app.format_result_summary')
    def test_merge_complete(self, mock_format_summary):
        """Test merge completion handler."""
        app = self._create_mock_app()
        app.is_processing = True
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=5,
            failed_rows=[]
        )
        mock_format_summary.return_value = "Summary text"
        
        app._merge_complete(result)
        
        assert app.is_processing is False
        app.run_button.configure.assert_called()
        app.status_label.configure.assert_called()
        mock_format_summary.assert_called_once_with(result)
    
    def test_merge_error(self):
        """Test merge error handler."""
        app = self._create_mock_app()
        app.is_processing = True
        app._log = MagicMock()
        app._update_ui_state = MagicMock()
        
        app._merge_error("Error message")
        
        assert app.is_processing is False
        app.run_button.configure.assert_called()
        app.status_label.configure.assert_called()
        app._log.assert_called()
    
    def test_update_ui_state_all_selected(self):
        """Test updating UI state when all paths are selected."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="normal")
    
    def test_update_ui_state_missing_paths(self):
        """Test updating UI state when paths are missing."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = None
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")
    
    def test_update_ui_state_processing(self):
        """Test updating UI state when processing."""
        app = self._create_mock_app()
        app.license_valid = True
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.is_processing = True
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")
    
    def test_update_ui_state_invalid_license(self):
        """Test updating UI state with invalid license."""
        app = self._create_mock_app()
        app.license_valid = False
        app.input_file_path = Path("/test.csv")
        app.pdf_dir_path = Path("/pdfs")
        app.output_dir_path = Path("/output")
        app.is_processing = False
        
        app._update_ui_state()
        
        app.run_button.configure.assert_called_once_with(state="disabled")


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
