"""
Configuration schema and validation.
Provides schema definitions and validation for application configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from .constants import Constants
from .logger import get_logger

logger = get_logger("config_schema")
DEFAULT_SERIAL_NUMBERS_COLUMN = Constants.DEFAULT_SERIAL_NUMBERS_COLUMN


@dataclass
class ConfigSchema:
    """Configuration schema with validation rules."""
    
    @staticmethod
    def validate_input_file(value: Optional[str]) -> Optional[str]:
        """
        Validate input file path.
        
        Args:
            value: Input file path string
            
        Returns:
            Validated path string or None
            
        Raises:
            ValueError: If path is invalid
        """
        if value is None or value == "":
            return None
        
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Input file does not exist: {value}")
        
        if not path.is_file():
            raise ValueError(f"Input file is not a file: {value}")
        
        return str(path.resolve())
    
    @staticmethod
    def validate_source_dir(value: Optional[str]) -> Optional[str]:
        """
        Validate source directory path.
        
        Args:
            value: Source directory path string
            
        Returns:
            Validated path string or None
            
        Raises:
            ValueError: If path is invalid
        """
        if value is None or value == "":
            return None
        
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Source directory does not exist: {value}")
        
        if not path.is_dir():
            raise ValueError(f"Source directory is not a directory: {value}")
        
        return str(path.resolve())
    
    @staticmethod
    def validate_output_dir(value: Optional[str]) -> Optional[str]:
        """
        Validate output directory path (will be created if it doesn't exist).
        
        Args:
            value: Output directory path string
            
        Returns:
            Validated path string or None
            
        Raises:
            ValueError: If path is invalid
        """
        if value is None or value == "":
            return None
        
        path = Path(value)
        # Output directory can be created, so we just validate the parent exists
        if path.exists() and not path.is_dir():
            raise ValueError(f"Output path exists but is not a directory: {value}")
        
        # Try to create parent if needed
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory: {e}")
        
        return str(path.resolve())
    
    @staticmethod
    def validate_column(value: Optional[str]) -> str:
        """
        Validate column name.
        
        Args:
            value: Column name string
            
        Returns:
            Validated column name
            
        Raises:
            ValueError: If column name is invalid
        """
        if value is None or value == "":
            return DEFAULT_SERIAL_NUMBERS_COLUMN
        
        # Column names should be non-empty strings
        if not isinstance(value, str) or len(value.strip()) == 0:
            raise ValueError(f"Column name must be a non-empty string: {value}")
        
        return value.strip()
    
    @staticmethod
    def validate_config(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate entire configuration dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValueError: If any configuration value is invalid
        """
        validated = {}
        
        # Validate input_file
        if 'input_file' in data:
            try:
                validated['input_file'] = ConfigSchema.validate_input_file(data['input_file'])
            except ValueError as e:
                logger.warning(f"Invalid input_file in config: {e}")
                validated['input_file'] = None
        
        # Validate pdf_dir (source_dir)
        if 'pdf_dir' in data:
            try:
                validated['pdf_dir'] = ConfigSchema.validate_source_dir(data['pdf_dir'])
            except ValueError as e:
                logger.warning(f"Invalid pdf_dir in config: {e}")
                validated['pdf_dir'] = None
        
        # Also handle source_dir alias
        if 'source_dir' in data and 'pdf_dir' not in validated:
            try:
                validated['pdf_dir'] = ConfigSchema.validate_source_dir(data['source_dir'])
            except ValueError as e:
                logger.warning(f"Invalid source_dir in config: {e}")
                validated['pdf_dir'] = None
        
        # Validate output_dir
        if 'output_dir' in data:
            try:
                validated['output_dir'] = ConfigSchema.validate_output_dir(data['output_dir'])
            except ValueError as e:
                logger.warning(f"Invalid output_dir in config: {e}")
                validated['output_dir'] = None
        
        # Validate required_column
        if 'required_column' in data:
            try:
                validated['required_column'] = ConfigSchema.validate_column(data['required_column'])
            except ValueError as e:
                logger.warning(f"Invalid required_column in config: {e}")
                validated['required_column'] = DEFAULT_SERIAL_NUMBERS_COLUMN
        else:
            validated['required_column'] = DEFAULT_SERIAL_NUMBERS_COLUMN
        
        return validated
