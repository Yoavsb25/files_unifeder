"""
Legacy and shared result types for the core package.
ProcessingResult is kept for backward compatibility; new code should use MergeResult from models.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ProcessingResult:
    """
    Legacy result of processing a file (total_rows, successful_merges, failed_rows).
    New code should use MergeResult from models package for detailed per-row results.
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
