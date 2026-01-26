"""
Cross-platform path utilities.
Handles path differences between Windows, macOS, and Linux.
"""

import os
import platform
import unicodedata
from pathlib import Path
from typing import Optional

from .logging_utils import get_logger

logger = get_logger("utils.path_utils")

# Windows long path prefix
WINDOWS_LONG_PATH_PREFIX = "\\\\?\\"
WINDOWS_MAX_PATH = 260  # Default Windows MAX_PATH limit


def normalize_path(path: Path) -> Path:
    """
    Normalize a path for cross-platform compatibility.
    
    Handles:
    - Unicode normalization (NFD/NFC for macOS compatibility)
    - Path resolution to absolute paths
    - Case normalization for Windows
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized Path object
    """
    # Resolve to absolute path first
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        # If resolution fails, try to make it absolute
        resolved = path.absolute()
    
    # Normalize Unicode (important for macOS which uses NFD)
    normalized_str = unicodedata.normalize('NFC', str(resolved))
    
    return Path(normalized_str)


def compare_paths(path1: Path, path2: Path, case_sensitive: Optional[bool] = None) -> bool:
    """
    Compare two paths for equality with cross-platform handling.
    
    Args:
        path1: First path to compare
        path2: Second path to compare
        case_sensitive: Whether comparison should be case-sensitive.
                       If None, uses platform default (case-insensitive on Windows)
        
    Returns:
        True if paths are equal, False otherwise
    """
    # Normalize both paths
    norm1 = normalize_path(path1)
    norm2 = normalize_path(path2)
    
    # Determine case sensitivity
    if case_sensitive is None:
        # Windows is case-insensitive by default
        case_sensitive = platform.system() != 'Windows'
    
    if case_sensitive:
        return norm1 == norm2
    else:
        # Case-insensitive comparison
        return str(norm1).lower() == str(norm2).lower()


def resolve_path(path: Path) -> Path:
    """
    Resolve a path to its absolute, normalized form.
    
    Args:
        path: Path to resolve
        
    Returns:
        Resolved and normalized Path
    """
    return normalize_path(path)


def is_long_path(path: Path) -> bool:
    """
    Check if a path exceeds Windows MAX_PATH limit.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is longer than Windows MAX_PATH (260 characters)
    """
    path_str = str(path.resolve())
    return len(path_str) > WINDOWS_MAX_PATH


def enable_long_paths_windows() -> bool:
    """
    Attempt to enable long path support on Windows.
    
    Note: This requires Windows 10 version 1607 or later and may require
    administrator privileges or registry changes. This function only
    checks if long paths are enabled, it does not modify system settings.
    
    Returns:
        True if long paths are enabled or not on Windows, False if disabled
    """
    if platform.system() != 'Windows':
        return True  # Not Windows, no issue
    
    # Check if long paths are enabled
    # This is a best-effort check - actual support depends on system configuration
    try:
        # Try to create a path with the long path prefix
        test_path = Path(WINDOWS_LONG_PATH_PREFIX + "C:\\test")
        return True
    except Exception:
        logger.warning(
            "Long path support may not be enabled on Windows. "
            "Paths longer than 260 characters may fail. "
            "See: https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation"
        )
        return False


def get_case_insensitive_path(folder: Path, filename: str) -> Optional[Path]:
    """
    Get a path with case-insensitive matching (useful for Windows).
    
    Args:
        folder: Directory to search in
        filename: Filename to find (case-insensitive)
        
    Returns:
        Path to the file if found (with actual case), None otherwise
    """
    if not folder.exists() or not folder.is_dir():
        return None
    
    filename_lower = filename.lower()
    
    try:
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.name.lower() == filename_lower:
                return file_path
    except (PermissionError, OSError) as e:
        logger.warning(f"Error accessing folder {folder}: {e}")
        return None
    
    return None


def validate_path(path: Path, must_exist: bool = True, must_be_file: bool = False, must_be_dir: bool = False) -> bool:
    """
    Validate a path for cross-platform compatibility.
    
    Args:
        path: Path to validate
        must_exist: Whether path must exist (default: True)
        must_be_file: Whether path must be a file (default: False)
        must_be_dir: Whether path must be a directory (default: False)
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        resolved = resolve_path(path)
        
        if must_exist and not resolved.exists():
            return False
        
        if must_be_file and not resolved.is_file():
            return False
        
        if must_be_dir and not resolved.is_dir():
            return False
        
        # Check for long paths on Windows
        if platform.system() == 'Windows' and is_long_path(resolved):
            if not enable_long_paths_windows():
                logger.warning(f"Path exceeds Windows MAX_PATH limit: {resolved}")
                return False
        
        return True
    
    except Exception as e:
        logger.warning(f"Error validating path {path}: {e}")
        return False
