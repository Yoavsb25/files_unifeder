"""
Legacy and shared result types for the core package.
ProcessingResult is deprecated; use MergeResult from models. Use as_processing_result() for legacy adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import MergeResult


@dataclass
class ProcessingResult:
    """
    **Deprecated.** Legacy result of processing a file (total_rows, successful_merges, failed_rows).
    Use MergeResult from pdf_merger.models for new code. For legacy callers that need this type,
    use as_processing_result(merge_result) after run_merge_job() or run_merge().
    """
    total_rows: int
    successful_merges: int
    failed_rows: List[int]

    def __str__(self) -> str:
        return (
            f"Total rows processed: {self.total_rows}\n"
            f"Successfully merged PDFs: {self.successful_merges}\n"
            f"Failed rows: {len(self.failed_rows)}"
        )


def as_processing_result(merge_result: "MergeResult") -> ProcessingResult:
    """Convert MergeResult to legacy ProcessingResult for backward compatibility."""
    return ProcessingResult(
        total_rows=merge_result.total_rows,
        successful_merges=merge_result.successful_merges,
        failed_rows=merge_result.failed_rows,
    )
