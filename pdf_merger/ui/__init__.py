"""
UI module.
Graphical user interface for PDF Merger.
"""

__all__ = [
    'run_gui',
]


def __getattr__(name: str):
    """Lazy-import run_gui so importing handlers does not load app/customtkinter."""
    if name == 'run_gui':
        from .app import run_gui
        return run_gui
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
