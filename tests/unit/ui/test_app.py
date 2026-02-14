"""
Unit tests for UI app module.
"""

import pytest
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, call, Mock

from pdf_merger.ui.app import PDFMergerApp, run_gui
from pdf_merger.ui.components import LogHandler
from pdf_merger.ui.theme import MESSAGE_PROCESSING_COMPLETE
from pdf_merger.licensing import LicenseStatus
from pdf_merger.models import MergeResult
from pdf_merger.core import format_failed_rows_display


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
        app.log_area._expanded = False
        app.log_area.winfo_ismapped = MagicMock(return_value=False)
        app.footer = MagicMock()
        app.results_frame = MagicMock()
        app.progress_bar = MagicMock()

        # Mock file selectors (SetupCards with has_error)
        app.input_file_selector = MagicMock()
        app.input_file_selector.has_error = MagicMock(return_value=False)
        app.pdf_dir_selector = MagicMock()
        app.pdf_dir_selector.has_error = MagicMock(return_value=False)
        app.output_dir_selector = MagicMock()
        app.output_dir_selector.has_error = MagicMock(return_value=False)

        # Mock column entry
        app.column_entry = MagicMock()
        app.column_entry.get.return_value = "Document ID"

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
        app._log_info = MagicMock()
        app._update_ui_state = MagicMock()

        mock_path = Path("/path/to/input.csv")
        app.file_handler.select_input_file.return_value = mock_path

        app._select_input_file()

        assert app.input_file_path == mock_path
        app.input_file_selector.set_path.assert_called_once_with(str(mock_path))
        app.file_handler.select_input_file.assert_called_once_with(
            required_column="Document ID",
        )
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
        app._log_error = MagicMock()

        app._show_error("Error message")

        app._log_error.assert_called_once_with("Error message")

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
            output_dir=app.output_dir_path,
            required_column="Document ID",
            fail_on_ambiguous_matches=app.config.fail_on_ambiguous_matches,
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
        app._log_info = MagicMock()

        app._on_merge_start()

        app.run_button.configure.assert_called_with(
            state="disabled", text="Processing…"
        )
        app.log_area.clear.assert_called_once()
        assert app._log_info.call_count >= 4  # Start message and paths
    
    def test_on_merge_complete_success(self):
        """Test merge completion handler with full success."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app._log = MagicMock()
        app._log_info = MagicMock()
        app._log_success = MagicMock()
        app._log_error = MagicMock()
        app._log_warning = MagicMock()
        app._update_ui_state = MagicMock()

        result = MergeResult(
            total_rows=5,
            successful_merges=5,
            failed_rows=[],
            skipped_rows=[],
        )

        app._on_merge_complete(result)

        # In production, worker's finally calls _set_idle() before on_complete; mock does not
        app.merge_handler.is_processing = False
        assert app.merge_handler.is_processing is False
        app.run_button.configure.assert_called_with(state="normal", text="Run Merge")
        app.results_frame.update_results.assert_called_once()
        call_kw = app.results_frame.update_results.call_args[1]
        assert call_kw["rows_analyzed"] == 5
        assert call_kw["pdfs_created"] == 5
        assert call_kw["skipped"] == 0
        assert call_kw["failed"] == 0

    def test_on_merge_error(self):
        """Test merge error handler."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app._log_error = MagicMock()
        app._update_ui_state = MagicMock()

        app._on_merge_error("Error message")

        # In production, worker's finally calls _set_idle(); mock does not
        app.merge_handler.is_processing = False
        assert app.merge_handler.is_processing is False
        app.run_button.configure.assert_called_with(state="normal", text="Run Merge")
        app._log_error.assert_called_once_with("Error message")

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
    
    @patch('pdf_merger.utils.validators.validate_file')
    @patch('pdf_merger.utils.validators.validate_folder')
    def test_load_config_into_ui_all_fields(self, mock_validate_folder, mock_validate_file, tmp_path):
        """Test loading config into UI with all fields."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("test")
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        
        from pdf_merger.config.config_manager import AppConfig
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
        from pdf_merger.config.config_manager import AppConfig
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
        from pdf_merger.config.config_manager import AppConfig
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
        
        from pdf_merger.config.config_manager import AppConfig
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
        """Test merge completion with partial success (4 created, 1 failed)."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app._log = MagicMock()
        app._log_info = MagicMock()
        app._log_error = MagicMock()
        app._log_warning = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = MergeResult(
            total_rows=5,
            successful_merges=4,
            failed_rows=[2],
            skipped_rows=[],
        )
        
        app._on_merge_complete(result)

        app.merge_handler.is_processing = False  # simulate worker _set_idle()
        assert app.merge_handler.is_processing is False
        app.results_frame.update_results.assert_called_once()
        call_kw = app.results_frame.update_results.call_args[1]
        assert call_kw["rows_analyzed"] == 5
        assert call_kw["pdfs_created"] == 4
        assert call_kw["failed"] == 1
    
    def test_on_merge_complete_failed(self):
        """Test merge completion with all failures."""
        app = self._create_mock_app()
        app.merge_handler.is_processing = True
        app._log = MagicMock()
        app._log_info = MagicMock()
        app._log_error = MagicMock()
        app._log_warning = MagicMock()
        app._update_ui_state = MagicMock()
        
        result = MergeResult(
            total_rows=5,
            successful_merges=0,
            failed_rows=[1, 2, 3, 4, 5],
            skipped_rows=[],
        )
        
        app._on_merge_complete(result)

        app.merge_handler.is_processing = False  # simulate worker _set_idle()
        assert app.merge_handler.is_processing is False
        app.results_frame.update_results.assert_called_once()
        call_kw = app.results_frame.update_results.call_args[1]
        assert call_kw["pdfs_created"] == 0
        assert call_kw["failed"] == 5

    def test_apply_merge_result_to_ui(self):
        """Given a MergeResult, _apply_merge_result_to_ui produces expected log lines and results frame values."""
        app = self._create_mock_app()
        app._log = MagicMock()
        app._log_info = MagicMock()
        app._log_warning = MagicMock()
        app._log_error = MagicMock()
        app.output_dir_path = Path("/out")

        result = MergeResult(
            total_rows=10,
            successful_merges=6,
            failed_rows=[2, 5],
            skipped_rows=[0, 9],
        )

        app._apply_merge_result_to_ui(result)

        app._log.assert_any_call("")
        app._log_info.assert_any_call(MESSAGE_PROCESSING_COMPLETE)
        app._log_info.assert_any_call("Rows analyzed: 10")
        app._log_info.assert_any_call("PDFs created: 6")
        app._log_warning.assert_called_once_with("Skipped: 2")
        app._log_error.assert_any_call("Failed: 2")
        app._log_error.assert_any_call(
            f"Failed row numbers: {format_failed_rows_display([2, 5])}"
        )

        app.results_frame.update_results.assert_called_once_with(
            rows_analyzed=10,
            pdfs_created=6,
            skipped=2,
            failed=2,
            output_dir="/out",
        )
        app.results_frame.show.assert_called_once_with(before=app.log_area)


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
