"""
Unit tests for core module __init__.
"""

import pytest
from pdf_merger.core import run_merge, format_result_summary, format_result_detailed


def test_core_exports():
    """Test that core module exports expected functions."""
    assert callable(run_merge)
    assert callable(format_result_summary)
    assert callable(format_result_detailed)
