"""
Protocols for operations layer.
Allows injecting test doubles for file system operations without touching the filesystem.
"""

from pathlib import Path
from typing import List, Optional, Protocol


class MergeOperations(Protocol):
    """
    Minimal interface for finding source files and merging PDFs.
    Implementations can be the real filesystem or test doubles.
    """

    def find_source_file(
        self,
        folder: Path,
        filename: str,
        fail_on_ambiguous: bool = False,
    ) -> Optional[Path]:
        """Find a source file (PDF or Excel) matching the filename in the folder."""
        ...

    def merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> bool:
        """Merge multiple PDF files into a single PDF at output_path."""
        ...
