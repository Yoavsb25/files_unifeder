"""
Event handlers for PDF Merger UI.
"""

import threading
import tkinter.filedialog as filedialog
from pathlib import Path
from typing import Callable, Optional

from ..utils.validators import validate_file, validate_folder
from ..utils.exceptions import PDFMergerError
from ..config.config_manager import resolve_required_column
from ..core import run_merge_job, format_result_summary
from ..core.types import ProgressCallback

from ..models import MergeResult
from ..utils.logging_utils import get_logger

logger = get_logger("pdf_merger.ui.handlers")

# MergeHandler state: single source of truth for "is a merge running"
_STATE_IDLE = "idle"
_STATE_RUNNING = "running"


class FileSelectionHandler:
    """Handler for file and directory selection. Validation errors use (field_id, message) with field_id one of FIELD_*."""

    FIELD_INPUT = "input_file"
    FIELD_SOURCE = "source_dir"
    FIELD_OUTPUT = "output_dir"

    def __init__(
        self,
        on_file_selected: Optional[Callable[[Path], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_validation_error: Optional[Callable[[str, str], None]] = None,
    ):
        self.on_file_selected = on_file_selected
        self.on_error = on_error
        self.on_validation_error = on_validation_error

    def _handle_error(self, message: str, field: str):
        """Dispatch error to validation or generic handler."""
        if self.on_validation_error:
            self.on_validation_error(field, message)
        if self.on_error:
            self.on_error(message)

    def select_input_file(
        self,
        required_column: Optional[str] = None,
    ) -> Optional[Path]:
        """Open file dialog to select input CSV/Excel file.

        Args:
            required_column: Column name for validation (uses default if None)

        Returns:
            Selected path if valid, None otherwise
        """
        column = resolve_required_column(required_column, None)
        file_path = filedialog.askopenfilename(
            title="Select CSV or Excel File",
            filetypes=[
                ("CSV/Excel files", "*.csv *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            path = Path(file_path)
            try:
                validate_file(path, required_column=column)
                if self.on_file_selected:
                    self.on_file_selected(path)
                return path
            except PDFMergerError as e:
                self._handle_error(str(e), self.FIELD_INPUT)
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
                field = self.FIELD_OUTPUT if not validate else self.FIELD_SOURCE
                self._handle_error(str(e), field)
                return None
        return None


class MergeHandler:
    """Handler for merge operations.

    Merge state is encapsulated: only _set_idle() and run_merge() transition state.
    UI reads is_processing (property). Worker must call _set_idle() in finally so
    the UI always reflects idle when the thread completes.
    """

    def __init__(
        self,
        on_start: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[MergeResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_progress: Optional[ProgressCallback] = None,
    ):
        self.on_start = on_start
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_progress = on_progress
        self._state = _STATE_IDLE
        self._job_id: Optional[str] = None

    @property
    def is_processing(self) -> bool:
        """True if a merge is currently running. Read-only; set only via _set_idle() and run_merge()."""
        return self._state == _STATE_RUNNING

    def _set_idle(self) -> None:
        """Transition to idle. Called from worker finally and ensures UI can re-enable Run Merge."""
        self._state = _STATE_IDLE
        self._job_id = None

    def run_merge(
        self,
        input_file: Path,
        pdf_dir: Path,
        output_dir: Path,
        required_column: Optional[str] = None,
        fail_on_ambiguous_matches: bool = True,
    ):
        """Run the merge operation in a separate thread."""
        if self.is_processing:
            return

        if not all([input_file, pdf_dir, output_dir]):
            if self.on_error:
                self.on_error("Please select all required files and directories.")
            return

        self._state = _STATE_RUNNING
        self._job_id = str(id(self))

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
        required_column: Optional[str],
        fail_on_ambiguous_matches: bool,
    ):
        """Worker thread for merge operation."""
        try:
            result = run_merge_job(
                input_file=input_file,
                pdf_dir=pdf_dir,
                output_dir=output_dir,
                required_column=resolve_required_column(required_column, None),
                fail_on_ambiguous=fail_on_ambiguous_matches,
                on_progress=self.on_progress,
            )

            if self.on_complete:
                self.on_complete(result)
        except Exception as e:
            error_msg = str(e)
            logger.exception("Merge operation failed")
            if self.on_error:
                self.on_error(error_msg)
        finally:
            self._set_idle()
    
    def format_result(self, result: MergeResult) -> str:
        """Format merge result as a summary string."""
        summary_text = format_result_summary(result)
        return summary_text
