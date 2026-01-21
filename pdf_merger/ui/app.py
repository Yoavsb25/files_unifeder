"""
CustomTkinter GUI application for PDF Merger.
"""

import threading
import tkinter.filedialog as filedialog
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from .. import APP_VERSION
from ..core import run_merge, format_result_summary, format_result_detailed
from ..licensing import LicenseManager, LicenseStatus
from ..logger import get_logger, setup_logger
from ..processor import ProcessingResult
from ..validators import validate_file, validate_folder

# Setup logging
setup_logger("pdf_merger", level=20)  # INFO level
logger = get_logger("ui.app")

# Set CustomTkinter appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class LogHandler:
    """Custom log handler that writes to GUI text widget."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = []
    
    def write(self, message: str):
        """Write log message to buffer."""
        if message.strip():
            self.buffer.append(message.strip())
    
    def flush(self):
        """Flush buffer to text widget."""
        if self.buffer:
            text = "\n".join(self.buffer)
            self.text_widget.insert("end", text + "\n")
            self.text_widget.see("end")
            self.buffer.clear()


class PDFMergerApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("PDF Batch Merger")
        self.geometry("800x700")
        self.minsize(600, 500)
        
        # License manager
        self.license_manager = LicenseManager(app_version=APP_VERSION)
        self.license_valid = False
        
        # Paths
        self.input_file_path: Optional[Path] = None
        self.pdf_dir_path: Optional[Path] = None
        self.output_dir_path: Optional[Path] = None
        
        # Processing state
        self.is_processing = False
        
        # Build UI
        self._build_ui()
        
        # Check license
        self._check_license()
    
    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="PDF Batch Merger",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # License status frame
        self.license_frame = ctk.CTkFrame(main_frame)
        self.license_frame.pack(fill="x", pady=(0, 20))
        self.license_label = ctk.CTkLabel(
            self.license_frame,
            text="Checking license...",
            font=ctk.CTkFont(size=12)
        )
        self.license_label.pack(pady=10)
        
        # File selection frame
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=(0, 10))
        
        # Input file
        input_frame = ctk.CTkFrame(file_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            input_frame,
            text="CSV/Excel File:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        input_button_frame = ctk.CTkFrame(input_frame)
        input_button_frame.pack(fill="x")
        
        self.input_file_label = ctk.CTkLabel(
            input_button_frame,
            text="No file selected",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.input_file_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            input_button_frame,
            text="Browse...",
            command=self._select_input_file,
            width=100
        ).pack(side="right")
        
        # PDF directory
        pdf_frame = ctk.CTkFrame(file_frame)
        pdf_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            pdf_frame,
            text="PDF Directory:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        pdf_button_frame = ctk.CTkFrame(pdf_frame)
        pdf_button_frame.pack(fill="x")
        
        self.pdf_dir_label = ctk.CTkLabel(
            pdf_button_frame,
            text="No directory selected",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.pdf_dir_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            pdf_button_frame,
            text="Browse...",
            command=self._select_pdf_directory,
            width=100
        ).pack(side="right")
        
        # Output directory
        output_frame = ctk.CTkFrame(file_frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            output_frame,
            text="Output Directory:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        output_button_frame = ctk.CTkFrame(output_frame)
        output_button_frame.pack(fill="x")
        
        self.output_dir_label = ctk.CTkLabel(
            output_button_frame,
            text="No directory selected",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.output_dir_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            output_button_frame,
            text="Browse...",
            command=self._select_output_directory,
            width=100
        ).pack(side="right")
        
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
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(
            log_frame,
            text="Output Log:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Footer with version
        footer_frame = ctk.CTkFrame(main_frame)
        footer_frame.pack(fill="x")
        
        version_label = ctk.CTkLabel(
            footer_frame,
            text=f"PDF Batch Merger v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        version_label.pack(side="left", padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            anchor="e"
        )
        self.status_label.pack(side="right", padx=10, pady=5)
    
    def _check_license(self):
        """Check license status and update UI."""
        status = self.license_manager.get_license_status()
        self.license_valid = (status == LicenseStatus.VALID)
        
        if status == LicenseStatus.VALID:
            info = self.license_manager.get_license_info()
            if info:
                self.license_label.configure(
                    text=f"✓ Licensed to: {info['company']} (Expires: {info['expires']})",
                    text_color="green"
                )
            else:
                self.license_label.configure(
                    text="✓ License valid",
                    text_color="green"
                )
        elif status == LicenseStatus.EXPIRED:
            self.license_label.configure(
                text="⚠ License expired - Merge functionality disabled",
                text_color="orange"
            )
        else:
            error_msg = self.license_manager.get_license_error_message(status)
            self.license_label.configure(
                text=f"✗ {error_msg}",
                text_color="red"
            )
        
        # Enable/disable merge button based on license
        self._update_ui_state()
    
    def _update_ui_state(self):
        """Update UI state based on license and selection."""
        can_run = (
            self.license_valid and
            self.input_file_path is not None and
            self.pdf_dir_path is not None and
            self.output_dir_path is not None and
            not self.is_processing
        )
        
        self.run_button.configure(state="normal" if can_run else "disabled")
    
    def _select_input_file(self):
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
            if validate_file(path):
                self.input_file_path = path
                self.input_file_label.configure(text=str(path))
                self._log(f"Selected input file: {path.name}")
                self._update_ui_state()
            else:
                self._log(f"Error: Invalid file selected")
                self._show_error("Invalid file. Please select a valid CSV or Excel file.")
    
    def _select_pdf_directory(self):
        """Open directory dialog to select PDF directory."""
        dir_path = filedialog.askdirectory(title="Select PDF Directory")
        
        if dir_path:
            path = Path(dir_path)
            if validate_folder(path, "PDF"):
                self.pdf_dir_path = path
                self.pdf_dir_label.configure(text=str(path))
                self._log(f"Selected PDF directory: {path}")
                self._update_ui_state()
            else:
                self._log(f"Error: Invalid directory selected")
                self._show_error("Invalid directory. Please select a valid directory.")
    
    def _select_output_directory(self):
        """Open directory dialog to select output directory."""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        
        if dir_path:
            path = Path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.output_dir_path = path
                self.output_dir_label.configure(text=str(path))
                self._log(f"Selected output directory: {path}")
                self._update_ui_state()
            except Exception as e:
                self._log(f"Error: Cannot create output directory: {e}")
                self._show_error(f"Cannot create output directory: {e}")
    
    def _log(self, message: str):
        """Add message to log area."""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        logger.info(message)
    
    def _show_error(self, message: str):
        """Show error message."""
        self._log(f"ERROR: {message}")
        self.status_label.configure(text="Error", text_color="red")
    
    def _run_merge(self):
        """Run the merge operation in a separate thread."""
        if not self.license_valid:
            self._show_error("License is not valid. Cannot run merge operation.")
            return
        
        if self.is_processing:
            return
        
        if not all([self.input_file_path, self.pdf_dir_path, self.output_dir_path]):
            self._show_error("Please select all required files and directories.")
            return
        
        # Disable UI
        self.is_processing = True
        self.run_button.configure(state="disabled", text="Processing...")
        self.status_label.configure(text="Processing...", text_color="blue")
        self.log_text.delete("1.0", "end")
        self._log("=" * 60)
        self._log("Starting merge operation...")
        self._log("=" * 60)
        self._log(f"Input file: {self.input_file_path}")
        self._log(f"PDF directory: {self.pdf_dir_path}")
        self._log(f"Output directory: {self.output_dir_path}")
        self._log("")
        
        # Run in separate thread
        thread = threading.Thread(target=self._merge_worker, daemon=True)
        thread.start()
    
    def _merge_worker(self):
        """Worker thread for merge operation."""
        try:
            result = run_merge(
                input_file=self.input_file_path,
                pdf_dir=self.pdf_dir_path,
                output_dir=self.output_dir_path
            )
            
            # Update UI in main thread
            self.after(0, self._merge_complete, result)
        except Exception as e:
            self.after(0, self._merge_error, str(e))
    
    def _merge_complete(self, result: ProcessingResult):
        """Handle merge completion."""
        self.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        
        self._log("")
        self._log("=" * 60)
        summary = format_result_summary(result)
        self._log(summary)
        
        if result.successful_merges == result.total_rows:
            self.status_label.configure(text="Success", text_color="green")
        elif result.successful_merges > 0:
            self.status_label.configure(text="Partial success", text_color="orange")
        else:
            self.status_label.configure(text="Failed", text_color="red")
        
        self._update_ui_state()
    
    def _merge_error(self, error_message: str):
        """Handle merge error."""
        self.is_processing = False
        self.run_button.configure(state="normal", text="Run Merge")
        
        self._log("")
        self._log("=" * 60)
        self._log(f"ERROR: {error_message}")
        self._log("=" * 60)
        
        self.status_label.configure(text="Error", text_color="red")
        self._update_ui_state()


def run_gui():
    """Run the GUI application."""
    app = PDFMergerApp()
    app.mainloop()
