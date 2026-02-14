"""
Shared type definitions for the core package.
"""

from typing import Callable, Literal

# Progress step literal: use these when invoking ProgressCallback so UI can distinguish loading vs processing.
ProgressStep = Literal["loading", "processing"]

# Progress callback: (step, current, total, message) -> None.
# step: PROGRESS_LOADING or PROGRESS_PROCESSING.
# current, total: Progress numerator and denominator (e.g. current row index and total rows).
# message: Human-readable status. Callbacks may run from a worker thread; UI must use thread-safe updates (e.g. after()).
ProgressCallback = Callable[[str, int, int, str], None]

PROGRESS_LOADING: ProgressStep = "loading"
PROGRESS_PROCESSING: ProgressStep = "processing"
