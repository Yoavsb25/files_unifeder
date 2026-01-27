#!/usr/bin/env python3
"""
Main entry point for PDF Merger.
Launches GUI application with license checking.
"""

import sys
import tkinter as tk
from tkinter import messagebox

from pdf_merger import APP_VERSION
from pdf_merger.licensing import LicenseManager, LicenseStatus
from pdf_merger.utils.logging_utils import setup_logger, get_logger
from pdf_merger.ui import run_gui
from pdf_merger.config.config_manager import load_config
from pdf_merger.observability import get_crash_reporter, get_metrics_collector, get_telemetry_service

# Setup logging
setup_logger("pdf_merger", level=20)  # INFO level
logger = get_logger("main")


def show_error_dialog(title: str, message: str):
    """
    Show an error dialog box.
    Works even when console=False in PyInstaller builds.
    """
    try:
        # Create a hidden root window for the messagebox
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front
        
        # Show error dialog
        messagebox.showerror(title, message)
        
        # Clean up
        root.destroy()
    except Exception as e:
        # Fallback: try to print to stderr (might work in some cases)
        logger.error(f"Failed to show error dialog: {e}")
        try:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"{title}", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(message, file=sys.stderr)
            print("="*60, file=sys.stderr)
        except Exception:
            pass  # Last resort - nothing we can do


def main():
    """Main entry point."""
    logger.info(f"PDF Batch Merger v{APP_VERSION} starting...")
    
    # Load configuration for observability settings
    config = load_config()
    
    # Initialize observability (opt-in)
    if config.crash_reporting_enabled:
        crash_reporter = get_crash_reporter(enabled=True)
        crash_reporter.install_exception_hook()
        logger.info("Crash reporting enabled")
    
    if config.metrics_enabled:
        get_metrics_collector(enabled=True)
        logger.debug("Metrics collection enabled")
    
    if config.telemetry_enabled:
        get_telemetry_service(enabled=True)
        logger.info("Telemetry enabled (opt-in)")
    
    # Check license
    license_manager = LicenseManager(app_version=APP_VERSION)
    license_status = license_manager.get_license_status()
    
    # Show expiry warning if applicable
    expiry_warning = license_manager.get_expiry_warning_message()
    if expiry_warning:
        logger.warning(f"License expiry warning: {expiry_warning}")
    
    if license_status == LicenseStatus.VALID:
        logger.info("License validated successfully")
        # Launch GUI
        try:
            run_gui()
        except Exception as e:
            logger.error(f"Error launching GUI: {e}")
            error_msg = f"An error occurred while starting the application:\n\n{str(e)}\n\nPlease contact support for assistance."
            show_error_dialog("Application Error", error_msg)
            sys.exit(1)
    else:
        # Invalid or expired license - show error dialog and exit
        error_msg = license_manager.get_license_error_message(license_status)
        
        # Get log file path for user reference
        try:
            from pathlib import Path
            log_file = Path.home() / '.pdf_merger' / 'logs' / 'pdf_merger.log'
            log_file_info = f"\n\nFor more details, check the log file at:\n{log_file}"
        except Exception:
            log_file_info = ""
        
        if license_status == LicenseStatus.EXPIRED:
            title = "License Expired"
            full_message = (
                "LICENSE EXPIRED\n\n"
                f"{error_msg}\n\n"
                "The application cannot run without a valid license.\n"
                "Please contact support for assistance."
                f"{log_file_info}"
            )
        else:
            title = "License Error"
            full_message = (
                "LICENSE ERROR\n\n"
                f"{error_msg}\n\n"
                "The application cannot run without a valid license.\n"
                "Please contact support for assistance."
                f"{log_file_info}"
            )
        
        logger.error(f"License validation failed: {license_status}")
        show_error_dialog(title, full_message)
        sys.exit(1)


if __name__ == '__main__':
    main()
