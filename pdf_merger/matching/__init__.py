"""
Matching rules package.
Formal matching rules for finding source files with ambiguity detection.
"""

from .rules import (
    MatchResult,
    MatchConfidence,
    find_matching_files,
    find_best_match,
    MatchBehavior
)

__all__ = [
    'MatchResult',
    'MatchConfidence',
    'find_matching_files',
    'find_best_match',
    'MatchBehavior',
]
