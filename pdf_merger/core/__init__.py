"""
Core logic module.
Decoupled business logic for UI consumption.
"""

from .merger import run_merge
from .reporter import format_result_summary, format_result_detailed

__all__ = [
    'run_merge',
    'format_result_summary',
    'format_result_detailed',
]
