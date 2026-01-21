#!/usr/bin/env python3
"""
Main entry point for PDF Merger.
Launches GUI application with license checking.
"""

import sys
from pathlib import Path

from pdf_merger import APP_VERSION
from pdf_merger.licensing import LicenseManager, LicenseStatus
from pdf_merger.logger import setup_logger, get_logger
from pdf_merger.ui import run_gui

# Setup logging
setup_logger("pdf_merger", level=20)  # INFO level
logger = get_logger("main")


def main():
    """Main entry point."""
    logger.info(f"PDF Batch Merger v{APP_VERSION} starting...")
    
    # Check license
    license_manager = LicenseManager(app_version=APP_VERSION)
    license_status = license_manager.get_license_status()
    
    if license_status == LicenseStatus.VALID:
        logger.info("License validated successfully")
        # Launch GUI
        try:
            run_gui()
        except Exception as e:
            logger.error(f"Error launching GUI: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    elif license_status == LicenseStatus.EXPIRED:
        # Show error but allow app to open (kill switch)
        error_msg = license_manager.get_license_error_message(license_status)
        print(f"\n{'='*60}")
        print("LICENSE EXPIRED")
        print("="*60)
        print(error_msg)
        print("="*60)
        print("\nThe application will open, but merge functionality is disabled.")
        print("Please contact support to renew your license.\n")
        
        # Still launch GUI (with disabled merge)
        try:
            run_gui()
        except Exception as e:
            logger.error(f"Error launching GUI: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Invalid license - show error and exit
        error_msg = license_manager.get_license_error_message(license_status)
        print(f"\n{'='*60}")
        print("LICENSE ERROR")
        print("="*60)
        print(error_msg)
        print("="*60)
        print("\nThe application cannot run without a valid license.")
        print("Please contact support for assistance.\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
