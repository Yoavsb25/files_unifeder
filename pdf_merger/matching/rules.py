"""
Formal matching rules implementation.
Provides deterministic file matching with ambiguity detection.
"""

import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

from ..logger import get_logger
from ..enums import SOURCE_FILE_EXTENSIONS

logger = get_logger("matching.rules")


class MatchConfidence(Enum):
    """Confidence level of a match."""
    EXACT = "exact"  # Exact filename match (case-insensitive)
    STEM = "stem"  # Stem match (filename without extension)
    LOW = "low"  # Low confidence match


class MatchBehavior(Enum):
    """Behavior when multiple matches are found."""
    FAIL_FAST = "fail_fast"  # Raise error on ambiguous matches (default for production)
    WARN_FIRST = "warn_first"  # Warn and use first match (development mode)
    LOG_ALL = "log_all"  # Log all matches for debugging


@dataclass
class MatchResult:
    """
    Result of a file matching operation.
    
    Attributes:
        file_path: Path to the matched file (None if no match)
        confidence: Confidence level of the match
        all_matches: List of all matching files (for ambiguity detection)
        is_ambiguous: Whether multiple matches were found
    """
    file_path: Optional[Path]
    confidence: MatchConfidence
    all_matches: List[Path]
    is_ambiguous: bool
    
    def __bool__(self) -> bool:
        """Return True if a match was found."""
        return self.file_path is not None


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode string for cross-platform compatibility.
    Uses NFC normalization (composed form) for consistency.
    
    Args:
        text: Input string
        
    Returns:
        Normalized string
    """
    return unicodedata.normalize('NFC', text)


def normalize_path_for_matching(path: Path) -> str:
    """
    Normalize a path for matching (case-insensitive, Unicode normalized).
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized string for comparison
    """
    # Normalize Unicode and convert to lowercase
    normalized = normalize_unicode(str(path))
    return normalized.lower()


def find_matching_files(
    folder: Path,
    filename: str,
    normalize_unicode_flag: bool = True
) -> List[Path]:
    """
    Find all files matching the given filename in the folder.
    
    This function returns ALL matches, allowing callers to handle ambiguity.
    
    Args:
        folder: Path to the folder containing source files
        filename: Filename (with or without extension) to search for
        normalize_unicode_flag: Whether to normalize Unicode (default: True)
        
    Returns:
        List of matching file paths, sorted alphabetically by full path
    """
    if not folder.exists() or not folder.is_dir():
        return []
    
    # Normalize input filename
    if normalize_unicode_flag:
        filename_normalized = normalize_unicode(filename)
    else:
        filename_normalized = filename
    filename_lower = filename_normalized.lower()
    filename_stem = Path(filename_normalized).stem.lower()
    
    matches = []
    
    # Iterate through all files in the folder
    try:
        for source_file in folder.iterdir():
            if not source_file.is_file():
                continue
            
            file_ext = source_file.suffix.lower()
            if file_ext not in SOURCE_FILE_EXTENSIONS:
                continue
            
            # Normalize file path for comparison
            if normalize_unicode_flag:
                file_name_normalized = normalize_path_for_matching(source_file)
            else:
                file_name_normalized = source_file.name.lower()
            
            file_stem_normalized = Path(file_name_normalized).stem.lower()
            
            # Check for exact match (case-insensitive, with or without extension)
            if file_name_normalized == filename_lower:
                matches.append(source_file)
            elif file_name_normalized == f"{filename_lower}{file_ext}":
                matches.append(source_file)
            # Check for stem match (filename without extension)
            elif file_stem_normalized == filename_stem:
                matches.append(source_file)
            elif file_stem_normalized == filename_lower:
                matches.append(source_file)
    
    except (PermissionError, OSError) as e:
        logger.warning(f"Error accessing folder {folder}: {e}")
        return []
    
    # Sort matches alphabetically by full path for deterministic behavior
    matches.sort(key=lambda p: str(p.resolve()))
    
    return matches


def find_best_match(
    folder: Path,
    filename: str,
    behavior: MatchBehavior = MatchBehavior.FAIL_FAST,
    normalize_unicode_flag: bool = True
) -> MatchResult:
    """
    Find the best matching file using formal matching rules.
    
    Matching Algorithm (in priority order):
    1. Exact match (case-insensitive, with any supported extension)
    2. Stem match (filename without extension, case-insensitive)
    3. Deterministic tie-breaking (alphabetical by full path)
    
    Args:
        folder: Path to the folder containing source files
        filename: Filename (with or without extension) to search for
        behavior: Behavior when multiple matches are found
        normalize_unicode_flag: Whether to normalize Unicode (default: True)
        
    Returns:
        MatchResult with the best match and ambiguity information
        
    Raises:
        ValueError: If behavior is FAIL_FAST and multiple matches are found
    """
    all_matches = find_matching_files(folder, filename, normalize_unicode_flag)
    
    if not all_matches:
        return MatchResult(
            file_path=None,
            confidence=MatchConfidence.LOW,
            all_matches=[],
            is_ambiguous=False
        )
    
    # Determine confidence level based on match type
    if normalize_unicode_flag:
        filename_normalized = normalize_unicode(filename)
    else:
        filename_normalized = filename
    filename_lower = filename_normalized.lower()
    filename_stem = Path(filename_normalized).stem.lower()
    
    # Check if we have exact matches
    exact_matches = []
    stem_matches = []
    
    for match in all_matches:
        if normalize_unicode_flag:
            match_name_normalized = normalize_path_for_matching(match)
        else:
            match_name_normalized = match.name.lower()
        
        match_stem_normalized = Path(match_name_normalized).stem.lower()
        
        # Exact match (full filename, case-insensitive)
        if (match_name_normalized == filename_lower or
            match_name_normalized == f"{filename_lower}{match.suffix.lower()}"):
            exact_matches.append(match)
        # Stem match
        elif match_stem_normalized == filename_stem or match_stem_normalized == filename_lower:
            stem_matches.append(match)
    
    # Prefer exact matches over stem matches
    if exact_matches:
        matches_to_use = exact_matches
        confidence = MatchConfidence.EXACT
    elif stem_matches:
        matches_to_use = stem_matches
        confidence = MatchConfidence.STEM
    else:
        matches_to_use = all_matches
        confidence = MatchConfidence.LOW
    
    # Handle ambiguity
    is_ambiguous = len(matches_to_use) > 1
    
    if is_ambiguous:
        if behavior == MatchBehavior.FAIL_FAST:
            match_paths_str = ', '.join(str(m) for m in matches_to_use)
            raise ValueError(
                f"Ambiguous match for '{filename}': multiple files found: {match_paths_str}"
            )
        elif behavior == MatchBehavior.WARN_FIRST:
            match_paths_str = ', '.join(str(m) for m in matches_to_use)
            logger.warning(
                f"Ambiguous match for '{filename}': multiple files found: {match_paths_str}. "
                f"Using first match: {matches_to_use[0]}"
            )
        elif behavior == MatchBehavior.LOG_ALL:
            logger.info(f"Ambiguous match for '{filename}': {len(matches_to_use)} matches found:")
            for i, match in enumerate(matches_to_use, 1):
                logger.info(f"  {i}. {match}")
    
    # Deterministic tie-breaking: use first match (already sorted alphabetically)
    best_match = matches_to_use[0] if matches_to_use else None
    
    return MatchResult(
        file_path=best_match,
        confidence=confidence,
        all_matches=all_matches,
        is_ambiguous=is_ambiguous
    )
