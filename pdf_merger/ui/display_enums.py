"""UI-only display enumerations (colors, status). Domain enums stay in core or models."""

from enum import Enum


class LicenseColor(Enum):
    """License status colors for UI display."""
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"


class StatusColor(Enum):
    """Status colors for UI components (footer, etc.)."""
    WHITE = "white"
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    BLUE = "blue"
