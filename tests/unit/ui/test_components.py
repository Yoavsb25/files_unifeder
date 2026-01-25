"""
Unit tests for UI components.
"""

import pytest
from unittest.mock import MagicMock, patch

# Mock tkinter before importing UI module
import sys
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

# Create mock classes for CustomTkinter
class MockCTk:
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
    def cget(self, *args, **kwargs):
        return "No selection"

class MockCTkButton:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
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

# Create mock_ctk module
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

from pdf_merger.ui.components import (
    LogHandler, FileSelector, LicenseFrame, LogArea, Footer
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


class TestFileSelector:
    """Test cases for FileSelector component."""
    
    def test_file_selector_initialization(self):
        """Test FileSelector initialization."""
        mock_parent = MagicMock()
        selector = FileSelector(mock_parent, "Test Label", "Browse...")
        
        assert selector.on_select is None
        assert selector.path_label is not None
        assert selector.browse_button is not None
    
    def test_file_selector_with_callback(self):
        """Test FileSelector with callback."""
        mock_parent = MagicMock()
        callback = MagicMock()
        selector = FileSelector(mock_parent, "Test Label", on_select=callback)
        
        selector._on_browse_clicked()
        
        callback.assert_called_once()
    
    def test_file_selector_set_path(self):
        """Test setting path in FileSelector."""
        mock_parent = MagicMock()
        selector = FileSelector(mock_parent, "Test Label")
        selector.path_label = MagicMock()
        
        selector.set_path("/test/path")
        
        selector.path_label.configure.assert_called_once_with(text="/test/path")
    
    def test_file_selector_get_path(self):
        """Test getting path from FileSelector."""
        mock_parent = MagicMock()
        selector = FileSelector(mock_parent, "Test Label")
        selector.path_label = MagicMock()
        selector.path_label.cget.return_value = "/test/path"
        
        path = selector.get_path()
        
        assert path == "/test/path"
        selector.path_label.cget.assert_called_once_with("text")


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


class TestFooter:
    """Test cases for Footer component."""
    
    def test_footer_initialization(self):
        """Test Footer initialization."""
        mock_parent = MagicMock()
        footer = Footer(mock_parent)
        
        assert footer.status_label is not None
    
    def test_footer_update_status(self):
        """Test updating footer status."""
        mock_parent = MagicMock()
        footer = Footer(mock_parent)
        footer.status_label = MagicMock()
        
        footer.update_status("Processing...", "blue")
        
        footer.status_label.configure.assert_called_once_with(
            text="Processing...",
            text_color="blue"
        )
