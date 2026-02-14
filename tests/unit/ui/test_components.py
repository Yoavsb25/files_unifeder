"""
Unit tests for UI components.
"""

import pytest
from unittest.mock import MagicMock, patch

from pdf_merger.ui.components import (
    LogHandler, SetupCard, LicenseFrame, LogArea, Footer
)


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


class TestSetupCard:
    """Test cases for SetupCard component."""

    def test_setup_card_initialization(self):
        """Test SetupCard initialization."""
        mock_parent = MagicMock()
        selector = SetupCard(mock_parent, 1, "Title", "Helper text")
        assert selector.on_select is None
        assert selector.path_entry is not None
        assert selector.browse_button is not None

    def test_setup_card_with_callback(self):
        """Test SetupCard with callback."""
        mock_parent = MagicMock()
        callback = MagicMock()
        selector = SetupCard(mock_parent, 1, "Title", "Helper", on_select=callback)
        selector._on_browse_clicked()
        callback.assert_called_once()

    def test_setup_card_set_path(self):
        """Test setting path in SetupCard."""
        mock_parent = MagicMock()
        selector = SetupCard(mock_parent, 1, "Title", "Helper")
        selector.path_entry = MagicMock()
        selector.set_path("/test/path")
        selector.path_entry.delete.assert_called_once_with(0, "end")
        selector.path_entry.insert.assert_called_once_with(0, "/test/path")

    def test_setup_card_get_path(self):
        """Test getting path from SetupCard."""
        mock_parent = MagicMock()
        selector = SetupCard(mock_parent, 1, "Title", "Helper")
        selector.path_entry = MagicMock()
        selector.path_entry.get.return_value = "/test/path"
        assert selector.get_path() == "/test/path"

    def test_setup_card_set_error_and_clear_error(self):
        """Test error state in SetupCard."""
        mock_parent = MagicMock()
        selector = SetupCard(mock_parent, 1, "Title", "Helper")
        selector.path_entry = MagicMock()
        selector.error_label = MagicMock()
        selector.set_error("Invalid path")
        selector.path_entry.configure.assert_called()
        selector.clear_error()
        selector.path_entry.configure.assert_called()


class TestLicenseFrame:
    """Test cases for LicenseFrame component."""
    
    def test_license_frame_initialization(self):
        """Test LicenseFrame initialization."""
        mock_parent = MagicMock()
        frame = LicenseFrame(mock_parent)
        
        assert frame.license_label is not None
    
    def test_license_frame_update_status(self):
        """Test updating license status."""
        mock_parent = MagicMock()
        frame = LicenseFrame(mock_parent)
        frame.license_label = MagicMock()
        
        frame.update_status("Test message", "green")
        
        frame.license_label.configure.assert_called_once_with(
            text="Test message",
            text_color="green"
        )


class TestLogArea:
    """Test cases for LogArea component."""
    
    def test_log_area_initialization(self):
        """Test LogArea initialization."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        
        assert log_area.log_text is not None
    
    def test_log_area_log(self):
        """Test logging to LogArea."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        log_area.log_text = MagicMock()
        
        log_area.log("Test message")
        
        log_area.log_text.insert.assert_called_once_with("end", "Test message\n")
        log_area.log_text.see.assert_called_once_with("end")
    
    def test_log_area_clear(self):
        """Test clearing LogArea."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        log_area.log_text = MagicMock()

        log_area.clear()

        log_area.log_text.delete.assert_called_once_with("1.0", "end")

    def test_log_area_log_success(self):
        """Test logging success message with styling."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        log_area.log_text = MagicMock()

        log_area.log_success("Merged successfully")

        log_area.log_text.insert.assert_called_once()
        args = log_area.log_text.insert.call_args[0]
        assert args[0] == "end"
        assert "Merged successfully" in args[1]
        assert "✓" in args[1]
        assert args[2] == LogArea.TAG_SUCCESS

    def test_log_area_log_error(self):
        """Test logging error message with styling."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        log_area.log_text = MagicMock()

        log_area.log_error("Failed to merge")

        log_area.log_text.insert.assert_called_once()
        args = log_area.log_text.insert.call_args[0]
        assert "Failed to merge" in args[1]
        assert "✗" in args[1]
        assert args[2] == LogArea.TAG_ERROR

    def test_log_area_log_info(self):
        """Test logging info message with styling."""
        mock_parent = MagicMock()
        log_area = LogArea(mock_parent)
        log_area.log_text = MagicMock()

        log_area.log_info("Reading input file")

        log_area.log_text.insert.assert_called_once()
        args = log_area.log_text.insert.call_args[0]
        assert "Reading input file" in args[1]
        assert "ⓘ" in args[1]
        assert args[2] == LogArea.TAG_INFO


class TestFooter:
    """Test cases for Footer component."""
    
    def test_footer_initialization(self):
        """Test Footer initialization."""
        mock_parent = MagicMock()
        footer = Footer(mock_parent)
        
        assert footer is not None

    def test_footer_update_status_no_op(self):
        """Footer.update_status is a no-op for backward compatibility."""
        mock_parent = MagicMock()
        footer = Footer(mock_parent)
        footer.update_status("Processing...", "blue")
        # No assertion - update_status does not configure any widget
