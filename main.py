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
from pdf_merger.config import load_config
from pdf_merger.observability import get_crash_reporter, get_metrics_collector, get_telemetry_service

# Setup logging
setup_logger("pdf_merger", level=20)  # INFO level
logger = get_logger("main")


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
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Invalid or expired license - show error and exit
        error_msg = license_manager.get_license_error_message(license_status)
        if license_status == LicenseStatus.EXPIRED:
            print(f"\n{'='*60}")
            print("LICENSE EXPIRED")
            print("="*60)
        else:
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
