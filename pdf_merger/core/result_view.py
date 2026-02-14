"""
Result view abstraction for formatting.
Provides a unified view over ProcessingResult and MergeResult so formatters
do not branch on isinstance. New result types can implement the same view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

from .constants import Constants

if TYPE_CHECKING:
    from .result_types import ProcessingResult
    from ..models import MergeResult, RowResult

PERCENTAGE_MULTIPLIER = Constants.PERCENTAGE_MULTIPLIER


@dataclass
class ResultView:
    """Unified view of processing result for formatting. Built from ProcessingResult or MergeResult."""
    total_rows: int
    successful_merges: int
    failed_rows: List[int]
    skipped_rows: List[int]
    success_rate: float
    row_results: List[RowResult]  # empty for legacy
    total_processing_time: Optional[float] = None


def as_result_view(result: Union[ProcessingResult, MergeResult]) -> ResultView:
    """Build a ResultView from either ProcessingResult or MergeResult."""
    from .result_types import ProcessingResult
    from ..models import MergeResult

    total_rows = result.total_rows
    successful = result.successful_merges
    failed_rows = result.failed_rows
    skipped_rows = getattr(result, "skipped_rows", []) or []
    if isinstance(result, MergeResult):
        success_rate = result.get_success_rate()
        row_results = getattr(result, "row_results", []) or []
        total_processing_time = getattr(result, "total_processing_time", None)
    else:
        success_rate = (successful / total_rows * PERCENTAGE_MULTIPLIER) if total_rows > 0 else 0.0
        row_results = []
        total_processing_time = None
    return ResultView(
        total_rows=total_rows,
        successful_merges=successful,
        failed_rows=failed_rows,
        skipped_rows=skipped_rows,
        success_rate=success_rate,
        row_results=row_results,
        total_processing_time=total_processing_time,
    )
