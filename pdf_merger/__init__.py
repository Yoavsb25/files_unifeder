"""
PDF Merger Package
A modular package for merging PDFs based on serial numbers from CSV/Excel files.

Public API (prefer these for external use; internal modules may change):
- run_merge, run_merge_job: Run merge operations (return MergeResult)
- load_config, AppConfig: Load and represent configuration
- MergeResult: Result type from merge runs (preferred); ProcessingResult deprecated
- as_processing_result: Adapter MergeResult -> ProcessingResult for legacy callers
- PDFMergerError: Base exception for error handling
"""

# Single source of version for releases; used by licensing and display
__version__ = '1.0.0'
APP_VERSION = __version__
APP_NAME = 'PDF Batch Merger'  # Application name for UI display

# Public API: high-level entry points and types only (internal refactors won't break callers)
from .core.merge_orchestrator import run_merge, run_merge_job
from .core.result_types import ProcessingResult, as_processing_result
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
    'as_processing_result',
    'PDFMergerError',
]
