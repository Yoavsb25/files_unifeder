"""
Unit tests for UI module exports.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Mock tkinter before importing UI module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()

from pdf_merger.ui import run_gui


def test_ui_exports():
    """Test that UI module exports expected functions."""
    assert callable(run_gui)
