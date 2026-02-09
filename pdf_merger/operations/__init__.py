"""
PDF operations module.
Handles PDF merging and Excel to PDF conversion.
Core depends on run_merge_for_row and MergeOperations only; concrete modules stay here.
"""

from .protocols import MergeOperations
from .row_merge import run_merge_for_row

__all__ = [
    "MergeOperations",
    "run_merge_for_row",
]
