"""
Pytest conftest for UI tests.
Mocks tkinter and CustomTkinter at module level so no display is required.
Loaded before any test in this directory; all UI tests share these mocks.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock


# Mock classes used by both test_app and test_components (union of required methods)
class MockCTk(object):
    """Mock CTk class for isinstance/issubclass checks."""
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
    def pack_forget(self, *args, **kwargs):
        pass
    def pack_propagate(self, *args, **kwargs):
        pass
    def winfo_ismapped(self):
        return False
    def grid(self, *args, **kwargs):
        pass
    def grid_rowconfigure(self, *args, **kwargs):
        pass
    def grid_columnconfigure(self, *args, **kwargs):
        pass


class MockCTkLabel:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def pack_forget(self, *args, **kwargs):
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
    def configure(self, *args, **kwargs):
        pass


class MockCTkEntry:
    def __init__(self, *args, **kwargs):
        self._text = ""
    def pack(self, *args, **kwargs):
        pass
    def delete(self, *args, **kwargs):
        pass
    def insert(self, index, text, *args):
        self._text = text
    def get(self):
        return self._text
    def configure(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
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
    def tag_config(self, *args, **kwargs):
        pass


class MockCTkProgressBar:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def pack_forget(self, *args, **kwargs):
        pass
    def start(self, *args, **kwargs):
        pass
    def stop(self, *args, **kwargs):
        pass


class MockCTkFont:
    def __init__(self, *args, **kwargs):
        pass
    @staticmethod
    def __call__(*args, **kwargs):
        return MagicMock()


# Patch sys.modules so UI imports get mocks (conftest loads before test modules)
mock_tkinter = MagicMock()
mock_tkinter.filedialog = MagicMock()
sys.modules['tkinter'] = mock_tkinter
sys.modules['tkinter.filedialog'] = mock_tkinter.filedialog

mock_ctk = ModuleType('customtkinter')
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkFrame
mock_ctk.CTkLabel = MockCTkLabel
mock_ctk.CTkButton = MockCTkButton
mock_ctk.CTkEntry = MockCTkEntry
mock_ctk.CTkTextbox = MockCTkTextbox
mock_ctk.CTkProgressBar = MockCTkProgressBar
mock_ctk.CTkFont = MockCTkFont
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
sys.modules['customtkinter'] = mock_ctk
