"""
Unit tests for utils package exports.
"""

import pytest
from pdf_merger.utils import (
    normalize_path,
    compare_paths,
    resolve_path,
    is_long_path,
    enable_long_paths_windows
)
from pathlib import Path


class TestUtilsInit:
    """Test cases for utils package initialization."""
    
    def test_imports_available(self):
        """Test that all expected functions are importable."""
        assert normalize_path is not None
        assert compare_paths is not None
        assert resolve_path is not None
        assert is_long_path is not None
        assert enable_long_paths_windows is not None
    
    def test_normalize_path_imported(self, tmp_path):
        """Test that normalize_path works when imported from package."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        result = normalize_path(test_file)
        
        assert result.is_absolute()
    
    def test_compare_paths_imported(self, tmp_path):
        """Test that compare_paths works when imported from package."""
        path1 = tmp_path / "test.txt"
        path2 = tmp_path / "test.txt"
        
        result = compare_paths(path1, path2)
        
        assert result is True
    
    def test_resolve_path_imported(self, tmp_path):
        """Test that resolve_path works when imported from package."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        result = resolve_path(test_file)
        
        assert result.is_absolute()
    
    def test_is_long_path_imported(self, tmp_path):
        """Test that is_long_path works when imported from package."""
        short_path = tmp_path / "test.txt"
        
        result = is_long_path(short_path)
        
        assert isinstance(result, bool)
    
    def test_enable_long_paths_windows_imported(self):
        """Test that enable_long_paths_windows works when imported from package."""
        result = enable_long_paths_windows()
        
        assert isinstance(result, bool)
