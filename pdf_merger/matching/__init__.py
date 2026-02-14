"""
Matching rules package.
File resolution policy lives here (find_best_match, find_matching_files);
file I/O and merge operations live in operations/. Matching changes (e.g. indexing)
should not leak into operations.
"""

from .rules import (
    MatchResult,
    find_matching_files,
    find_best_match,
)
from ..core.enums import MatchConfidence, MatchBehavior

__all__ = [
    'MatchResult',
    'MatchConfidence',
    'find_matching_files',
    'find_best_match',
    'MatchBehavior',
]
