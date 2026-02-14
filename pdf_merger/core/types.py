"""
Shared type definitions for the core package.
"""

from typing import Callable

# Progress callback contract:
#   Signature: (step: str, current: int, total: int, message: str) -> None
#   step: One of PROGRESS_LOADING, PROGRESS_PROCESSING (used to show loading vs row-by-row progress).
#   current, total: Progress numerator and denominator (e.g. current row index and total rows).
#   message: Human-readable status (e.g. "Processing Row 3... (GRNW_1, GRNW_2)").
#   Threading: Callbacks may be invoked from a worker thread; UI must use thread-safe updates (e.g. after()).
ProgressCallback = Callable[[str, int, int, str], None]

# Progress step names. Valid values: PROGRESS_LOADING, PROGRESS_PROCESSING.
# Used by merge_processor (process_job) and UI (app._schedule_progress) to coordinate
# progress bar and messages. Add new steps here if extending progress reporting.
PROGRESS_LOADING = "loading"
PROGRESS_PROCESSING = "processing"
