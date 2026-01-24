"""
Configuration management module.
Handles loading and saving application configuration.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .enums import DEFAULT_SERIAL_NUMBERS_COLUMN
from .logger import get_logger

logger = get_logger("config")


@dataclass
class AppConfig:
    """Application configuration."""
    input_file: Optional[str] = None
    pdf_dir: Optional[str] = None
    output_dir: Optional[str] = None
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Create config from dictionary."""
        return cls(
            input_file=data.get('input_file'),
            pdf_dir=data.get('pdf_dir'),
            output_dir=data.get('output_dir'),
            required_column=data.get('required_column', DEFAULT_SERIAL_NUMBERS_COLUMN)
        )
    
    def get_input_file_path(self) -> Optional[Path]:
        """Get input file as Path object."""
        return Path(self.input_file) if self.input_file else None
    
    def get_pdf_dir_path(self) -> Optional[Path]:
        """Get PDF directory as Path object."""
        return Path(self.pdf_dir) if self.pdf_dir else None
    
    def get_output_dir_path(self) -> Optional[Path]:
        """Get output directory as Path object."""
        return Path(self.output_dir) if self.output_dir else None


def get_config_path() -> Path:
    """
    Get the path to the configuration file.
    
    Returns:
        Path to config.json (in app directory or user home)
    """
    # Try app directory first (for packaged app)
    app_dir = Path(__file__).parent.parent
    app_config = app_dir / 'config.json'
    if app_config.exists():
        return app_config
    
    # Fall back to user home directory
    home_dir = Path.home()
    config_dir = home_dir / '.pdf_merger'
    config_dir.mkdir(exist_ok=True)
    return config_dir / 'config.json'


def load_config() -> AppConfig:
    """
    Load configuration from file.
    
    Returns:
        AppConfig object (default if file doesn't exist)
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        logger.info(f"Config file not found at {config_path}, using defaults")
        return AppConfig()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = AppConfig.from_dict(data)
        logger.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Error loading config from {config_path}: {e}, using defaults")
        return AppConfig()


def save_config(config: AppConfig) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: AppConfig object to save
        
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()
    
    try:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        return False
