"""
Matching rules package.
Formal matching rules for finding source files with ambiguity detection.
"""

from .rules import (
    MatchResult,
    find_matching_files,
    find_matching_files_from_index,
    find_best_match,
    find_best_match_from_index,
    build_source_index,
    SourceFileIndex,
)
from ..core.enums import MatchConfidence, MatchBehavior

__all__ = [
    'MatchResult',
    'MatchConfidence',
    'find_matching_files',
    'find_matching_files_from_index',
    'find_best_match',
    'find_best_match_from_index',
    'build_source_index',
    'SourceFileIndex',
    'MatchBehavior',
]
