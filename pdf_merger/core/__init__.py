"""
Core logic module.
Workflow and data: merge orchestration, serial number parsing, CSV/Excel reading,
result reporting. (File-format operations live in operations/.)
"""

from .merge_orchestrator import run_merge, run_merge_job
from .result_reporter import format_result_summary, format_result_detailed, format_failed_rows_display

__all__ = [
    'run_merge',
    'run_merge_job',
    'format_result_summary',
    'format_result_detailed',
    'format_failed_rows_display',
]
