"""
Domain enums for PDF Merger models.
RowStatus is used by MergeResult/RowResult and is owned by the domain layer.
MatchConfidence and MatchBehavior are used by the matching layer for file matching.
"""

from enum import Enum


class MatchConfidence(Enum):
    """Confidence level of a match."""
    EXACT = "exact"
    STEM = "stem"
    LOW = "low"


class MatchBehavior(Enum):
    """Behavior when multiple matches are found."""
    FAIL_FAST = "fail_fast"
    WARN_FIRST = "warn_first"
    LOG_ALL = "log_all"


class RowStatus(Enum):
    """Status of a row processing operation."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"
