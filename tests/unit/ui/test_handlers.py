"""
Unit tests for UI handlers.
"""

import pytest
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Mock tkinter before importing UI module
import sys
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

from pdf_merger.ui.handlers import FileSelectionHandler, MergeHandler
from pdf_merger.core.merge_processor import ProcessingResult
from pdf_merger.utils.exceptions import PDFMergerError


class TestFileSelectionHandler:
    """Test cases for FileSelectionHandler."""
    
    def test_handler_initialization(self):
        """Test FileSelectionHandler initialization."""
        handler = FileSelectionHandler()
        
        assert handler.on_file_selected is None
        assert handler.on_error is None
    
    def test_handler_initialization_with_callbacks(self):
        """Test FileSelectionHandler initialization with callbacks."""
        on_file = MagicMock()
        on_error = MagicMock()
        handler = FileSelectionHandler(
            on_file_selected=on_file,
            on_error=on_error
        )
        
        assert handler.on_file_selected == on_file
        assert handler.on_error == on_error
    
    @patch('pdf_merger.ui.handlers.filedialog.askopenfilename')
    @patch('pdf_merger.ui.handlers.validate_file')
    def test_select_input_file_success(self, mock_validate, mock_dialog):
        """Test selecting input file successfully."""
        mock_validate.return_value = None
        mock_dialog.return_value = "/path/to/input.csv"
        on_file = MagicMock()
        
        handler = FileSelectionHandler(on_file_selected=on_file)
        result = handler.select_input_file()
        
        assert result == Path("/path/to/input.csv")
        on_file.assert_called_once_with(Path("/path/to/input.csv"))
        mock_validate.assert_called_once_with(Path("/path/to/input.csv"))
    
    @patch('pdf_merger.ui.handlers.filedialog.askopenfilename')
    @patch('pdf_merger.ui.handlers.validate_file')
    def test_select_input_file_cancelled(self, mock_validate, mock_dialog):
        """Test cancelling file selection."""
        mock_dialog.return_value = ""
        
        handler = FileSelectionHandler()
        result = handler.select_input_file()
        
        assert result is None
        mock_validate.assert_not_called()
    
    @patch('pdf_merger.ui.handlers.filedialog.askopenfilename')
    @patch('pdf_merger.ui.handlers.validate_file')
    def test_select_input_file_invalid(self, mock_validate, mock_dialog):
        """Test selecting invalid input file."""
        error = PDFMergerError("Invalid file")
        mock_validate.side_effect = error
        mock_dialog.return_value = "/path/to/invalid.txt"
        on_error = MagicMock()
        
        handler = FileSelectionHandler(on_error=on_error)
        result = handler.select_input_file()
        
        assert result is None
        on_error.assert_called_once_with("Invalid file: Invalid file")
    
    @patch('pdf_merger.ui.handlers.filedialog.askdirectory')
    @patch('pdf_merger.ui.handlers.validate_folder')
    def test_select_directory_success(self, mock_validate, mock_dialog):
        """Test selecting directory successfully."""
        mock_validate.return_value = None
        mock_dialog.return_value = "/path/to/dir"
        on_file = MagicMock()
        
        handler = FileSelectionHandler(on_file_selected=on_file)
        result = handler.select_directory(
            title="Select Directory",
            validate=True,
            folder_type="Source"
        )
        
        assert result == Path("/path/to/dir")
        on_file.assert_called_once_with(Path("/path/to/dir"))
        mock_validate.assert_called_once_with(Path("/path/to/dir"), "Source")
    
    @patch('pdf_merger.ui.handlers.filedialog.askdirectory')
    def test_select_directory_no_validate(self, mock_dialog, tmp_path):
        """Test selecting directory without validation."""
        output_dir = tmp_path / "output"
        mock_dialog.return_value = str(output_dir)
        on_file = MagicMock()
        
        handler = FileSelectionHandler(on_file_selected=on_file)
        result = handler.select_directory(
            title="Select Output",
            validate=False
        )
        
        assert result == output_dir
        on_file.assert_called_once_with(output_dir)
        assert output_dir.exists()
    
    @patch('pdf_merger.ui.handlers.filedialog.askdirectory')
    @patch('pdf_merger.ui.handlers.validate_folder')
    def test_select_directory_invalid(self, mock_validate, mock_dialog):
        """Test selecting invalid directory."""
        error = PDFMergerError("Invalid directory")
        mock_validate.side_effect = error
        mock_dialog.return_value = "/path/to/invalid"
        on_error = MagicMock()
        
        handler = FileSelectionHandler(on_error=on_error)
        result = handler.select_directory(validate=True, folder_type="Source")
        
        assert result is None
        on_error.assert_called_once()
    
    @patch('pdf_merger.ui.handlers.filedialog.askdirectory')
    def test_select_directory_creation_error(self, mock_dialog):
        """Test directory selection when creation fails."""
        mock_dialog.return_value = "/path/to/output"
        on_error = MagicMock()
        
        handler = FileSelectionHandler(on_error=on_error)
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            result = handler.select_directory(validate=False)
            
            assert result is None
            on_error.assert_called_once()


class TestMergeHandler:
    """Test cases for MergeHandler."""
    
    def test_handler_initialization(self):
        """Test MergeHandler initialization."""
        handler = MergeHandler()
        
        assert handler.on_start is None
        assert handler.on_complete is None
        assert handler.on_error is None
        assert handler.is_processing is False
    
    def test_handler_initialization_with_callbacks(self):
        """Test MergeHandler initialization with callbacks."""
        on_start = MagicMock()
        on_complete = MagicMock()
        on_error = MagicMock()
        
        handler = MergeHandler(
            on_start=on_start,
            on_complete=on_complete,
            on_error=on_error
        )
        
        assert handler.on_start == on_start
        assert handler.on_complete == on_complete
        assert handler.on_error == on_error
    
    def test_run_merge_missing_paths(self):
        """Test running merge with missing paths."""
        handler = MergeHandler()
        
        handler.run_merge(
            input_file=None,
            pdf_dir=Path("/pdfs"),
            output_dir=Path("/output")
        )
        
        assert handler.is_processing is False
    
    def test_run_merge_already_processing(self):
        """Test running merge when already processing."""
        handler = MergeHandler()
        handler.is_processing = True
        
        handler.run_merge(
            input_file=Path("/test.csv"),
            pdf_dir=Path("/pdfs"),
            output_dir=Path("/output")
        )
        
        # Should not start another merge
        assert handler.is_processing is True
    
    @patch('pdf_merger.ui.handlers.run_merge')
    def test_run_merge_success(self, mock_run_merge, tmp_path):
        """Test running merge operation successfully."""
        on_start = MagicMock()
        on_complete = MagicMock()
        
        handler = MergeHandler(
            on_start=on_start,
            on_complete=on_complete
        )
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=5,
            failed_rows=[]
        )
        mock_run_merge.return_value = result
        
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        handler.run_merge(input_file, pdf_dir, output_dir)
        
        # Wait for thread to complete
        import time
        time.sleep(0.1)
        
        assert handler.is_processing is False
        on_start.assert_called_once()
        on_complete.assert_called_once_with(result)
        mock_run_merge.assert_called_once_with(
            input_file=input_file,
            pdf_dir=pdf_dir,
            output_dir=output_dir
        )
    
    @patch('pdf_merger.ui.handlers.run_merge')
    def test_run_merge_error(self, mock_run_merge, tmp_path):
        """Test running merge operation with error."""
        on_start = MagicMock()
        on_error = MagicMock()
        
        handler = MergeHandler(
            on_start=on_start,
            on_error=on_error
        )
        
        mock_run_merge.side_effect = ValueError("Processing error")
        
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        handler.run_merge(input_file, pdf_dir, output_dir)
        
        # Wait for thread to complete
        import time
        time.sleep(0.1)
        
        assert handler.is_processing is False
        on_start.assert_called_once()
        on_error.assert_called_once_with("Processing error")
    
    def test_format_result(self):
        """Test formatting merge result."""
        handler = MergeHandler()
        
        result = ProcessingResult(
            total_rows=5,
            successful_merges=3,
            failed_rows=[2, 4]
        )
        
        with patch('pdf_merger.ui.handlers.format_result_summary') as mock_format:
            mock_format.return_value = "Summary text"
            summary = handler.format_result(result)
            
            assert summary == "Summary text"
            mock_format.assert_called_once_with(result)
