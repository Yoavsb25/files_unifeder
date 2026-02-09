"""
Unit tests for logging_utils module.
"""

import pytest
import logging
import sys
from unittest.mock import patch, MagicMock
from pdf_merger.utils.logging_utils import setup_logger, get_logger


class TestSetupLogger:
    """Test cases for setup_logger function."""
    
    def test_setup_logger_defaults(self):
        """Test creating a logger with default parameters (stream handler; file handler if writable)."""
        # Use a unique name so we get a fresh logger not shared with other tests
        logger = setup_logger(name="test_defaults_logger")
        
        assert logger.name == "test_defaults_logger"
        assert logger.level == logging.INFO
        # setup_logger adds at least console handler; file handler added when log dir is writable
        assert len(logger.handlers) >= 1
        # Console handler is StreamHandler to stdout (FileHandler is also a StreamHandler subclass)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout]
        assert len(console_handlers) == 1
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        if file_handlers:
            assert "pdf_merger.log" in str(file_handlers[0].baseFilename)
    
    def test_setup_logger_custom_name(self):
        """Test creating a logger with custom name."""
        logger = setup_logger(name="custom_logger")
        
        assert logger.name == "custom_logger"
        assert logger.level == logging.INFO
    
    def test_setup_logger_custom_level(self):
        """Test creating a logger with custom level."""
        # Use a unique name to avoid conflicts with other tests
        logger = setup_logger(name="test_debug_logger", level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG
    
    def test_setup_logger_formatter(self):
        """Test that logger has correct formatter."""
        logger = setup_logger(name="test_formatter_logger")
        # Console handler is StreamHandler to stdout (FileHandler is also a StreamHandler subclass)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout]
        assert len(console_handlers) == 1
        handler = console_handlers[0]
        
        assert handler.formatter is not None
        assert isinstance(handler.formatter, logging.Formatter)
        assert handler.formatter._fmt == '%(levelname)s - %(message)s'
    
    def test_setup_logger_idempotent(self):
        """Test that calling setup_logger multiple times doesn't add duplicate handlers."""
        logger1 = setup_logger(name="test_logger")
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger(name="test_logger")
        
        assert logger1 is logger2  # Should return same logger instance
        assert len(logger2.handlers) == initial_handler_count  # Should not add duplicate handlers
    
    def test_setup_logger_logging_output(self, capsys):
        """Test that logger actually outputs messages."""
        logger = setup_logger(name="test_output")
        logger.info("Test message")
        
        captured = capsys.readouterr()
        assert "INFO - Test message" in captured.out


class TestGetLogger:
    """Test cases for get_logger function."""
    
    def test_get_logger_no_name(self):
        """Test getting logger without specifying name."""
        logger = get_logger()
        
        assert logger.name == "pdf_merger"
    
    def test_get_logger_with_name(self):
        """Test getting logger with module name."""
        logger = get_logger("test_module")
        
        assert logger.name == "pdf_merger.test_module"
    
    def test_get_logger_none_name(self):
        """Test getting logger with None as name."""
        logger = get_logger(None)
        
        assert logger.name == "pdf_merger"
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module1")
        
        assert logger1 is logger2
