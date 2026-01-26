"""
Logging utilities for PDF Merger.
Provides centralized logging setup and management.
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "pdf_merger", level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a logger instance.
    
    Args:
        name: Logger name (default: "pdf_merger")
        level: Logging level (default: logging.INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Optional module name. If None, uses "pdf_merger"
        
    Returns:
        Logger instance
    """
    if name is None:
        name = "pdf_merger"
    else:
        # Ensure logger is a child of main logger
        name = f"pdf_merger.{name}"
    
    return logging.getLogger(name)
