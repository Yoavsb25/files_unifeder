"""
Shared type definitions for the core package.
"""

from typing import Callable

# (step: str, current: int, total: int, message: str) -> None
ProgressCallback = Callable[[str, int, int, str], None]
