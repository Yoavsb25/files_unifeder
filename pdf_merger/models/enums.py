"""
Domain enums for PDF Merger models.
RowStatus is used by MergeResult/RowResult and is owned by the domain layer.
"""

from enum import Enum


class RowStatus(Enum):
    """Status of a row processing operation."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"
