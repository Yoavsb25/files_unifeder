"""
UI module.
Graphical user interface for PDF Merger.
"""

from .app import run_gui
from .enums import LicenseColor, WarningLevel, StatusColor

__all__ = [
    'run_gui',
]
