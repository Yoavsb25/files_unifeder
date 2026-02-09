"""
Event handlers for PDF Merger UI.
"""

import threading
import tkinter.filedialog as filedialog
from pathlib import Path
from typing import Optional, Callable

from ..utils.validators import validate_file, validate_folder
from ..utils.exceptions import PDFMergerError
from ..core import run_merge_job, format_result_summary
from ..models import MergeResult
from ..utils.logging_utils import get_logger

logger = get_logger("ui.handlers")


class FileSelectionHandler:
    """Handler for file and directory selection."""
    
    def __init__(
        self,
        on_file_selected: Optional[Callable[[Path], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        self.on_file_selected = on_file_selected
        self.on_error = on_error
    
    def select_input_file(self) -> Optional[Path]:
        """Open file dialog to select input CSV/Excel file."""
        file_path = filedialog.askopenfilename(
            title="Select CSV or Excel File",
            filetypes=[
                ("CSV/Excel files", "*.csv *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            path = Path(file_path)
            try:
                validate_file(path)
                if self.on_file_selected:
                    self.on_file_selected(path)
                return path
            except PDFMergerError as e:
                if self.on_error:
                    self.on_error(f"Invalid file: {e}")
                return None
        return None
    
    def select_directory(
        self,
        title: str = "Select Directory",
        validate: bool = True,
        folder_type: str = "Source"
    ) -> Optional[Path]:
        """Open directory dialog to select a directory."""
        dir_path = filedialog.askdirectory(title=title)
        
        if dir_path:
            path = Path(dir_path)
            try:
                if validate:
                    validate_folder(path, folder_type)
                else:
                    # For output directory, just ensure it can be created
                    path.mkdir(parents=True, exist_ok=True)
                
                if self.on_file_selected:
                    self.on_file_selected(path)
                return path
            except (PDFMergerError, Exception) as e:
                if self.on_error:
                    self.on_error(f"Invalid directory: {e}")
                return None
        return None


class MergeHandler:
    """Handler for merge operations. Uses run_merge_job (single entry point) and forwards config."""

    def __init__(
        self,
        on_start: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[MergeResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.on_start = on_start
        self.on_complete = on_complete
        self.on_error = on_error
        self.is_processing = False

    def run_merge(
        self,
        input_file: Path,
        pdf_dir: Path,
        output_dir: Path,
        required_column: str = "serial_numbers",
        fail_on_ambiguous_matches: bool = True,
    ):
        """Run the merge operation in a separate thread. Config (column, ambiguous behavior) is forwarded."""
        if self.is_processing:
            return

        if not all([input_file, pdf_dir, output_dir]):
            if self.on_error:
                self.on_error("Please select all required files and directories.")
            return

        self.is_processing = True

        if self.on_start:
            self.on_start()

        thread = threading.Thread(
            target=self._merge_worker,
            args=(input_file, pdf_dir, output_dir, required_column, fail_on_ambiguous_matches),
            daemon=True,
        )
        thread.start()

    def _merge_worker(
        self,
        input_file: Path,
        pdf_dir: Path,
        output_dir: Path,
        required_column: str,
        fail_on_ambiguous_matches: bool,
    ):
        """Worker thread: run_merge_job (single entry point) then adapt result for UI."""
        try:
            result = run_merge_job(
                input_file=input_file,
                pdf_dir=pdf_dir,
                output_dir=output_dir,
                required_column=required_column,
                fail_on_ambiguous=fail_on_ambiguous_matches,
            )
            if self.on_complete:
                self.on_complete(result)
        except Exception as e:
            error_msg = str(e)
            logger.exception("Merge operation failed")
            if self.on_error:
                self.on_error(error_msg)
        finally:
            self.is_processing = False

    def format_result(self, result: MergeResult) -> str:
        """Format merge result as a summary string (MergeResult is the single source of truth)."""
        return format_result_summary(result)
