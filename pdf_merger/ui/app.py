"""
CustomTkinter GUI application for PDF Merger.
"""

from pathlib import Path
from typing import Optional

import customtkinter as ctk

from .. import APP_VERSION
from ..licensing import LicenseManager
from ..logger import get_logger, setup_logger
from ..processor import ProcessingResult
from ..config import load_config
from .components import FileSelector, LicenseFrame, LogArea, Footer
from .license_ui import update_license_display
from .handlers import FileSelectionHandler, MergeHandler
from ..enums import StatusColor

# Setup logging
setup_logger("pdf_merger", level=20)
logger = get_logger("ui.app")

# Set CustomTkinter appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_NAME = "PDF Batch Merger"


class PDFMergerApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title(APP_NAME)
        self.geometry("800x700")
        self.minsize(600, 500)
        
        # License manager
        self.license_manager = LicenseManager(app_version=APP_VERSION)
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
            on_error=self._show_error
        )
        
        self.merge_handler = MergeHandler(
            on_start=self._on_merge_start,
            on_complete=self._on_merge_complete,
            on_error=self._on_merge_error
        )
    
    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # License status frame
        self.license_frame = LicenseFrame(main_frame)
        self.license_frame.pack(fill="x", pady=(0, 20))
        
        # File selection frame
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=(0, 10))
        
        # Input file selector
        self.input_file_selector = FileSelector(
            file_frame,
            label_text="CSV/Excel File:",
            on_select=self._select_input_file
        )
        self.input_file_selector.pack(fill="x", padx=10, pady=10)
        
        # PDF directory selector
        self.pdf_dir_selector = FileSelector(
            file_frame,
            label_text="Source Directory:",
            on_select=self._select_pdf_directory
        )
        self.pdf_dir_selector.pack(fill="x", padx=10, pady=10)
        
        # Output directory selector
        self.output_dir_selector = FileSelector(
            file_frame,
            label_text="Output Directory:",
            on_select=self._select_output_directory
        )
        self.output_dir_selector.pack(fill="x", padx=10, pady=10)
        
        # Run button
        self.run_button = ctk.CTkButton(
            main_frame,
            text="Run Merge",
            command=self._run_merge,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.run_button.pack(fill="x", pady=(10, 10))
        
        # Log/output area
        self.log_area = LogArea(main_frame)
        self.log_area.pack(fill="both", expand=True, pady=(0, 10))
        
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
    
    def _load_config_into_ui(self):
        """Load configuration values into UI fields if available."""
        if self.config.input_file:
            try:
                path = Path(self.config.input_file)
                if path.exists():
                    from ..validators import validate_file
                    validate_file(path)
                    self.input_file_path = path
                    self.input_file_selector.set_path(str(path))
                    logger.info(f"Loaded input file from config: {path}")
            except Exception as e:
                logger.warning(f"Could not load input file from config: {e}")
        
        if self.config.pdf_dir:
            try:
                path = Path(self.config.pdf_dir)
                if path.exists():
                    from ..validators import validate_folder
                    validate_folder(path, "Source")
                    self.pdf_dir_path = path
                    self.pdf_dir_selector.set_path(str(path))
                    logger.info(f"Loaded source directory from config: {path}")
            except Exception as e:
                logger.warning(f"Could not load source directory from config: {e}")
        
        if self.config.output_dir:
            try:
                path = Path(self.config.output_dir)
                path.mkdir(parents=True, exist_ok=True)
                self.output_dir_path = path
                self.output_dir_selector.set_path(str(path))
                logger.info(f"Loaded output directory from config: {path}")
            except Exception as e:
                logger.warning(f"Could not load output directory from config: {e}")
        
        # Update UI state after loading config
        self._update_ui_state()
    
    def _update_ui_state(self):
        """Update UI state based on license and selection."""
        can_run = (
            self.license_valid and
            self.input_file_path is not None and
            self.pdf_dir_path is not None and
            self.output_dir_path is not None and
            not self.merge_handler.is_processing
        )
        
        self.run_button.configure(state="normal" if can_run else "disabled")
    
    
    def _select_input_file(self):
        """Open file dialog to select input CSV/Excel file."""
        path = self.file_handler.select_input_file()
        if path:
            self.input_file_path = path
            self.input_file_selector.set_path(str(path))
            self._log(f"Selected input file: {path.name}")
            self._update_ui_state()
    
    def _select_pdf_directory(self):
        """Open directory dialog to select source directory."""
        path = self.file_handler.select_directory(
            title="Select Source Directory (PDF and Excel files)",
            validate=True,
            folder_type="Source"
        )
        if path:
            self.pdf_dir_path = path
            self.pdf_dir_selector.set_path(str(path))
            self._log(f"Selected source directory: {path}")
            self._update_ui_state()
    
    def _select_output_directory(self):
        """Open directory dialog to select output directory."""
        path = self.file_handler.select_directory(
            title="Select Output Directory",
            validate=False
        )
        if path:
            self.output_dir_path = path
            self.output_dir_selector.set_path(str(path))
            self._log(f"Selected output directory: {path}")
            self._update_ui_state()
    
    def _log(self, message: str):
        """Add message to log area."""
        self.log_area.log(message)
        logger.info(message)
    
    def _show_error(self, message: str):
        """Show error message."""
        self._log(f"ERROR: {message}")
        self.footer.update_status("Error", StatusColor.RED)
    
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
            output_dir=self.output_dir_path
        )
    
    def _on_merge_start(self):
        """Handle merge operation start."""
        self.run_button.configure(state="disabled", text="Processing...")
        self.footer.update_status("Processing...", StatusColor.BLUE)
        self.log_area.clear()
        self._log("=" * 60)
        self._log("Starting merge operation...")
        self._log("=" * 60)
        self._log(f"Input file: {self.input_file_path}")
        self._log(f"Source directory: {self.pdf_dir_path}")
        self._log(f"Output directory: {self.output_dir_path}")
        self._log("")
    
    def _on_merge_complete(self, result: ProcessingResult):
        """Handle merge completion."""
        # Reset processing state
        self.merge_handler.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        
        self._log("")
        self._log("=" * 60)
        summary = self.merge_handler.format_result(result)
        self._log(summary)
        
        if result.successful_merges == result.total_rows:
            self.footer.update_status("Success", StatusColor.GREEN)
        elif result.successful_merges > 0:
            self.footer.update_status("Partial success", StatusColor.ORANGE)
        else:
            self.footer.update_status("Failed", StatusColor.RED)
        
        self._update_ui_state()
    
    def _on_merge_error(self, error_message: str):
        """Handle merge error."""
        # Reset processing state
        self.merge_handler.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        
        self._log("")
        self._log("=" * 60)
        self._log(f"ERROR: {error_message}")
        self._log("=" * 60)
        
        self.footer.update_status("Error", StatusColor.RED)
        self._update_ui_state()


def run_gui():
    """Run the GUI application."""
    app = PDFMergerApp()
    app.mainloop()
