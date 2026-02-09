"""
Core logic module.
Decoupled business logic for UI consumption.
"""

from .merge_orchestrator import run_merge, run_merge_job
from .result_reporter import format_result_summary, format_result_detailed

__all__ = [
    "run_merge",
    "run_merge_job",
    "format_result_summary",
    "format_result_detailed",
]
