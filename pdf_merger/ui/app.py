"""
CustomTkinter GUI application for PDF Merger.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk

from ..core.constants import Constants
from ..core.types import PROGRESS_LOADING, PROGRESS_PROCESSING

from .. import APP_VERSION
from ..licensing import LicenseManager
from ..utils.logging_utils import get_logger, setup_logger
from ..models import MergeResult
from ..config.config_manager import load_config, save_config, resolve_required_column
from .components import SetupCard, LicenseFrame, LogArea, ResultsFrame, Footer, bind_focus_highlight
from .license_ui import update_license_display
from .handlers import FileSelectionHandler, MergeHandler
from .theme import (
    CORNER_RADIUS,
    SECTION_SPACING,
    CARD_SPACING,
    CONTENT_MAX_WIDTH,
    APP_BACKGROUND,
    CARD_BG,
    CARD_BORDER,
    FONT_TITLE_SIZE,
    FONT_LABEL_SIZE,
    FONT_MONO_SIZE,
    INPUT_BACKGROUND,
    PRIMARY_BLUE,
    PRIMARY_BLUE_HOVER,
)
# Setup logging
setup_logger("pdf_merger", level=20)
logger = get_logger("pdf_merger.ui.app")

# Set CustomTkinter appearance - dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

APP_NAME = "PDF Batch Merger"


class PDFMergerApp(ctk.CTk):
    """Main application window."""

    def __init__(self, license_manager: Optional[LicenseManager] = None):
        super().__init__()
        
        self.title(APP_NAME)
        self.geometry("1020x800")
        self.minsize(620, 500)
        self.configure(fg_color=APP_BACKGROUND)
        
        # If license_manager is provided, the app does not re-validate at startup (main passes it in after validation).
        self.license_manager = license_manager or LicenseManager(app_version=APP_VERSION)
        self.license_valid = False
        
        # Paths
        self.input_file_path: Optional[Path] = None
        self.pdf_dir_path: Optional[Path] = None
        self.output_dir_path: Optional[Path] = None
        
        # Load configuration
        self.config = load_config(start_path=Path.cwd())
        
        # Initialize handlers
        self._init_handlers()
        
        # Build UI
        self._build_ui()
        
        # Load config values into UI if available
        self._load_config_into_ui()
        
        # Check license
        self._check_license()
    
    def _init_handlers(self):
        """Initialize event handlers."""
        self.file_handler = FileSelectionHandler(
            on_error=self._show_error,
            on_validation_error=self._on_validation_error,
        )
        
        self.merge_handler = MergeHandler(
            on_start=self._on_merge_start,
            on_complete=self._on_merge_complete,
            on_error=self._on_merge_error,
            on_progress=self._schedule_progress,
        )
    
    def _build_ui(self):
        """Build the user interface."""
        # Use grid for responsive layout - content expands with window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Outer frame (32px margin)
        outer_frame = ctk.CTkFrame(self, fg_color="transparent")
        outer_frame.grid(row=0, column=0, sticky="nsew", padx=32, pady=32)
        outer_frame.grid_rowconfigure(0, weight=1)
        outer_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable content area - enables scrolling when content exceeds window
        self.scrollable_frame = ctk.CTkScrollableFrame(
            outer_frame,
            fg_color="transparent",
            scrollbar_button_color=CARD_BG,
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Inner content - fills scrollable area, scrolls when content exceeds window
        main_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=APP_BACKGROUND,
            corner_radius=CORNER_RADIUS,
        )
        main_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title (Header Section)
        title_label = ctk.CTkLabel(
            main_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold")
        )
        title_label.pack(pady=(0, SECTION_SPACING))
        
        # License status frame
        self.license_frame = LicenseFrame(main_frame)
        self.license_frame.pack(fill="x", pady=(0, SECTION_SPACING))

        # Serial numbers column row (packed inside Instructions File card via extra_row)
        column_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        ctk.CTkLabel(
            column_frame,
            text="Serial numbers column:",
            font=ctk.CTkFont(size=FONT_LABEL_SIZE, weight="bold"),
        ).pack(anchor="w", side="left", padx=(0, 8))
        self.column_entry = ctk.CTkEntry(
            column_frame,
            placeholder_text="e.g. serial_numbers or Document ID",
            font=ctk.CTkFont(family="Courier New", size=FONT_MONO_SIZE),
            width=220,
            height=40,
            fg_color=INPUT_BACKGROUND,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.column_entry.pack(side="left")
        bind_focus_highlight(self.column_entry)

        # Setup Section - three step-based cards (Instructions File includes serial column row)
        self.input_file_selector = SetupCard(
            main_frame,
            step_number=1,
            title="Instructions File",
            helper_text="Must include a serial_numbers column (or Document ID)",
            on_select=self._select_input_file,
            extra_row=column_frame,
        )
        self.input_file_selector.pack(fill="x", pady=(0, CARD_SPACING))

        self.pdf_dir_selector = SetupCard(
            main_frame,
            step_number=2,
            title="Source Directory",
            helper_text="All referenced PDFs & Excel files must live here",
            on_select=self._select_pdf_directory,
        )
        self.pdf_dir_selector.pack(fill="x", pady=(0, CARD_SPACING))

        self.output_dir_selector = SetupCard(
            main_frame,
            step_number=3,
            title="Output Directory",
            helper_text="Merged PDFs will be saved here",
            on_select=self._select_output_directory,
        )
        self.output_dir_selector.pack(fill="x", pady=(0, SECTION_SPACING))

        # Run button (Run Section) - primary blue, full width, 54px
        self.run_button = ctk.CTkButton(
            main_frame,
            text="Run Merge",
            command=self._run_merge,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=54,
            corner_radius=CORNER_RADIUS,
            fg_color=PRIMARY_BLUE,
            hover_color=PRIMARY_BLUE_HOVER,
            text_color="white",
            cursor="hand2",
        )
        self.run_button.pack(fill="x", pady=(SECTION_SPACING, 8))

        # Loading progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            mode="indeterminate",
            height=6,
            corner_radius=3,
        )
        self.progress_bar.pack(fill="x", pady=(0, SECTION_SPACING))
        self.progress_bar.pack_forget()

        # Results section (hidden until first run)
        self.results_frame = ResultsFrame(
            main_frame,
            on_open_output=self._open_output_folder,
            on_toggle_log=self._toggle_detailed_log,
        )

        # Log/output area
        self.log_area = LogArea(main_frame)
        self.log_area.pack(fill="both", expand=True, pady=(0, SECTION_SPACING))
        
        # Footer
        self.footer = Footer(main_frame)
        self.footer.pack(fill="x")
    
    def _check_license(self):
        """Check license status and update UI."""
        self.license_valid = update_license_display(
            self.license_manager,
            self.license_frame.license_label
        )
        self._update_ui_state()
    
    def _apply_path_config(
        self,
        path_str: Optional[str],
        path_attr: str,
        selector: Any,
        validator: Callable[[Path], None],
        log_label: str,
    ) -> None:
        """Apply one path from config: validate, set path attribute and selector, log. Swallows exceptions and logs warning."""
        if not path_str:
            return
        try:
            path = Path(path_str)
            validator(path)
            setattr(self, path_attr, path)
            selector.set_path(str(path))
            logger.info(f"Loaded {log_label} from config: {path}")
        except Exception as e:
            logger.warning(f"Could not load {log_label} from config: {e}")

    def _load_config_into_ui(self):
        """Load configuration values into UI fields if available."""
        from ..utils.validators import validate_file, validate_folder

        self.column_entry.insert(0, self.config.required_column)

        def validate_input(p: Path) -> None:
            if p.exists():
                validate_file(p, required_column=self.config.required_column)

        def validate_source(p: Path) -> None:
            if p.exists():
                validate_folder(p, "Source")

        def validate_output(p: Path) -> None:
            p.mkdir(parents=True, exist_ok=True)

        self._apply_path_config(
            self.config.input_file, "input_file_path", self.input_file_selector, validate_input, "input file"
        )
        self._apply_path_config(
            self.config.pdf_dir, "pdf_dir_path", self.pdf_dir_selector, validate_source, "source directory"
        )
        self._apply_path_config(
            self.config.output_dir, "output_dir_path", self.output_dir_selector, validate_output, "output directory"
        )
        self._update_ui_state()
    
    def _has_validation_errors(self) -> bool:
        """Return True if any setup card has a validation error."""
        return (
            self.input_file_selector.has_error()
            or self.pdf_dir_selector.has_error()
            or self.output_dir_selector.has_error()
        )

    def _get_run_block_reasons(self) -> list:
        """Return list of reasons Run Merge is disabled (empty if allowed). Use for tooltips/debugging."""
        reasons = []
        if not self.license_valid:
            reasons.append("License invalid")
        if self.input_file_path is None:
            reasons.append("Select input file")
        if self.pdf_dir_path is None:
            reasons.append("Select source directory")
        if self.output_dir_path is None:
            reasons.append("Select output directory")
        if self._has_validation_errors():
            reasons.append("Fix validation errors")
        if self.merge_handler.is_processing:
            reasons.append("Merge in progress")
        return reasons

    def _can_run_merge(self) -> bool:
        """True if Run Merge is allowed: valid license, all paths set, no validation errors, not already processing."""
        return len(self._get_run_block_reasons()) == 0

    def _update_ui_state(self):
        """Update UI state based on license, selection, and validation."""
        self.run_button.configure(state="normal" if self._can_run_merge() else "disabled")
    
    
    def _get_column(self) -> str:
        """Get column name from entry, or default if empty. Uses resolve_required_column for consistent resolution."""
        return resolve_required_column(self.column_entry.get(), self.config.required_column)

    def _on_validation_error(self, field: str, message: str):
        """Handle validation error - show inline on the affected selector."""
        selector_map = {
            FileSelectionHandler.FIELD_INPUT: self.input_file_selector,
            FileSelectionHandler.FIELD_SOURCE: self.pdf_dir_selector,
            FileSelectionHandler.FIELD_OUTPUT: self.output_dir_selector,
        }
        selector = selector_map.get(field)
        if selector:
            selector.set_error(message)
        self._update_ui_state()

    def _select_input_file(self):
        """Open file dialog to select input CSV/Excel file."""
        path = self.file_handler.select_input_file(
            required_column=self._get_column(),
        )
        if path:
            self.input_file_path = path
            self.input_file_selector.set_path(str(path))
            self.input_file_selector.clear_error()
            self.config = self.config.merge(type(self.config)(input_file=str(path)))
            save_config(self.config)
            self._log_info(f"Selected input file: {path.name}")
            self._update_ui_state()

    def _select_pdf_directory(self):
        """Open directory dialog to select source directory."""
        path = self.file_handler.select_directory(
            title="Select Source Directory (PDF and Excel files)",
            validate=True,
            folder_type="Source",
        )
        if path:
            self.pdf_dir_path = path
            self.pdf_dir_selector.set_path(str(path))
            self.pdf_dir_selector.clear_error()
            self.config = self.config.merge(type(self.config)(pdf_dir=str(path)))
            save_config(self.config)
            self._log_info(f"Selected source directory: {path}")
            self._update_ui_state()

    def _open_output_folder(self, path: str):
        """Open the output folder in the system file manager. Uses OS-specific command (open/explorer/xdg-open)."""
        folder = Path(path)
        if not folder.exists():
            return
        if sys.platform == "darwin":
            subprocess.run(["open", str(folder)], check=False)
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(folder)], check=False)
        else:
            subprocess.run(["xdg-open", str(folder)], check=False)

    def _toggle_detailed_log(self):
        """Toggle visibility of the detailed log area (expand/collapse)."""
        self.log_area._toggle()
        self.results_frame.view_log_btn.configure(
            text="Hide Detailed Log" if self.log_area._expanded else "View Detailed Log"
        )

    def _select_output_directory(self):
        """Open directory dialog to select output directory."""
        path = self.file_handler.select_directory(
            title="Select Output Directory",
            validate=False,
        )
        if path:
            self.output_dir_path = path
            self.output_dir_selector.set_path(str(path))
            self.output_dir_selector.clear_error()
            self.config = self.config.merge(type(self.config)(output_dir=str(path)))
            save_config(self.config)
            self._log_info(f"Selected output directory: {path}")
            self._update_ui_state()
    
    def _log(self, message: str):
        """Add plain message to log area."""
        self.log_area.log(message)
        logger.info(message)

    def _log_info(self, message: str):
        """Add info message with styling."""
        self.log_area.log_info(message)
        logger.info(message)

    def _log_success(self, message: str):
        """Add success message with styling."""
        self.log_area.log_success(message)
        logger.info(message)

    def _log_error(self, message: str):
        """Add error message with styling."""
        self.log_area.log_error(message)
        logger.error(message)

    def _log_warning(self, message: str):
        """Add warning message with styling."""
        self.log_area.log_warning(message)
        logger.warning(message)

    def _schedule_progress(
        self, step: str, current: int, total: int, message: str
    ):
        """Schedule progress update on main thread (called from worker)."""
        self.after(
            0,
            lambda s=step, c=current, t=total, m=message: self._on_merge_progress(
                s, c, t, m
            ),
        )

    def _on_merge_progress(
        self, step: str, current: int, total: int, message: str
    ):
        """Handle progress update from merge operation."""
        if step == PROGRESS_LOADING:
            self._log_info(message)
            return
        if step != PROGRESS_PROCESSING:
            self._log_info(message)
            return
        # Map keywords to log method for processing step
        log_by_keyword = [
            ("Success", self._log_success),
            ("Skipped", self._log_warning),
            ("Failed", self._log_error),
        ]
        for keyword, log_fn in log_by_keyword:
            if keyword in message:
                log_fn(message)
                return
        if message.strip().startswith("•"):
            self._log_warning(message)
        else:
            self._log_info(message)

    def _show_error(self, message: str):
        """Show error message."""
        self._log_error(message)

    def _run_merge(self):
        """Run the merge operation."""
        if not self.license_valid:
            self._show_error("License is not valid. Cannot run merge operation.")
            return
        
        if not all([self.input_file_path, self.pdf_dir_path, self.output_dir_path]):
            self._show_error("Please select all required files and directories.")
            return
        
        self.merge_handler.run_merge(
            input_file=self.input_file_path,
            pdf_dir=self.pdf_dir_path,
            output_dir=self.output_dir_path,
            required_column=self._get_column(),
            fail_on_ambiguous_matches=self.config.fail_on_ambiguous_matches,
        )
    
    def _on_merge_start(self):
        """Handle merge operation start."""
        self.run_button.configure(state="disabled", text="Processing…")
        self.progress_bar.pack(fill="x", pady=(0, SECTION_SPACING), before=self.log_area)
        self.progress_bar.start()
        self.results_frame.hide()
        self.log_area.clear()
        self._log_info("Starting merge operation...")
        self._log_info(f"Input file: {self.input_file_path}")
        self._log_info(f"Source directory: {self.pdf_dir_path}")
        self._log_info(f"Output directory: {self.output_dir_path}")
        self._log("")
    
    def _on_merge_complete(self, result: MergeResult):
        """Handle merge completion - accurate Rows Analyzed, PDFs Created, Skipped, Failed."""
        self.merge_handler.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        self._log("")
        self._log_info("Processing Complete")
        self._log_info(f"Rows analyzed: {result.total_rows}")
        self._log_info(f"PDFs created: {result.successful_merges}")
        skipped_count = len(result.skipped_rows)
        failed_count = len(result.failed_rows)
        if skipped_count > 0:
            self._log_warning(f"Skipped: {skipped_count}")
        if failed_count > 0:
            self._log_error(f"Failed: {failed_count}")
        if result.failed_rows:
                failed_str = ", ".join(map(str, result.failed_rows))
                max_len = Constants.MAX_DISPLAY_STRING_LENGTH
                if len(failed_str) > max_len:
                    failed_str = failed_str[: max_len - 3] + "..."
                self._log_error(f"Failed row numbers: {failed_str}")

        self.results_frame.update_results(
            rows_analyzed=result.total_rows,
            pdfs_created=result.successful_merges,
            skipped=skipped_count,
            failed=failed_count,
            output_dir=str(self.output_dir_path) if self.output_dir_path else None,
        )
        self.results_frame.show(before=self.log_area)
        self._update_ui_state()
    
    def _on_merge_error(self, error_message: str):
        """Handle merge error."""
        self.merge_handler.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        self._log("")
        self._log_error(error_message)
        self._update_ui_state()


def run_gui(license_manager: Optional[LicenseManager] = None):
    """Run the GUI application.

    Args:
        license_manager: Optional pre-validated LicenseManager instance.
            When provided (e.g. from main.py), avoids duplicate license validation at startup.
    """
    app = PDFMergerApp(license_manager=license_manager)
    app.mainloop()
