"""
Utilities package.
Cross-platform utilities and helpers.
"""

from .path_utils import (
    normalize_path,
    compare_paths,
    resolve_path,
    is_long_path,
    enable_long_paths_windows,
)
from .exceptions import PDFMergerError, PDFMergerFileNotFoundError

__all__ = [
    'normalize_path',
    'compare_paths',
    'resolve_path',
    'is_long_path',
    'enable_long_paths_windows',
    'PDFMergerError',
    'PDFMergerFileNotFoundError',
]
