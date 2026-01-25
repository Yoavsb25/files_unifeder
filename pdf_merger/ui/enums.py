"""
UI-specific enumerations for PDF Merger application.
"""

from enum import Enum


class LicenseColor(Enum):
    """License status colors for UI display."""
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"


class WarningLevel(Enum):
    """License expiry warning levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class StatusColor(Enum):
    """Status colors for UI components (footer, etc.)."""
    WHITE = "white"
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    BLUE = "blue"
