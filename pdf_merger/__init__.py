"""
PDF Merger Package
A modular package for merging PDFs based on serial numbers from CSV/Excel files.

Public API (prefer these for external use; internal modules may change):
- run_merge, run_merge_job: Run merge operations (orchestrator)
- load_config, AppConfig: Load and represent configuration
- MergeResult, ProcessingResult: Result types from merge runs
- PDFMergerError: Base exception for error handling
"""

__version__ = '1.0.0'
APP_VERSION = '1.0.0'  # Application version for licensing and display
APP_NAME = 'PDF Batch Merger'  # Application name for UI display

# Public API: high-level entry points and types only (internal refactors won't break callers)
from .core.merge_orchestrator import run_merge, run_merge_job
from .core.merge_processor import ProcessingResult
from .config.config_manager import load_config, AppConfig
from .models import MergeResult
from .utils.exceptions import PDFMergerError

__all__ = [
    'APP_VERSION',
    'APP_NAME',
    'run_merge',
    'run_merge_job',
    'load_config',
    'AppConfig',
    'MergeResult',
    'ProcessingResult',
    'PDFMergerError',
]
