"""
Configuration management module.
Handles loading and saving application configuration with precedence support.

Configuration Precedence (highest to lowest):
1. Environment variables
2. User config file (~/.pdf_merger/config.json or app directory)
3. Per-project preset (.pdf_merger_config.json in project directory)
4. Defaults
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any

from .enums import DEFAULT_SERIAL_NUMBERS_COLUMN
from .logger import get_logger
from .config_schema import ConfigSchema

logger = get_logger("config")

# Environment variable names
ENV_INPUT_FILE = 'PDF_MERGER_INPUT_FILE'
ENV_SOURCE_DIR = 'PDF_MERGER_SOURCE_DIR'
ENV_OUTPUT_DIR = 'PDF_MERGER_OUTPUT_DIR'
ENV_COLUMN = 'PDF_MERGER_COLUMN'

# Per-project preset filename
PROJECT_PRESET_FILENAME = '.pdf_merger_config.json'


@dataclass
class AppConfig:
    """Application configuration."""
    input_file: Optional[str] = None
    pdf_dir: Optional[str] = None
    output_dir: Optional[str] = None
    required_column: str = DEFAULT_SERIAL_NUMBERS_COLUMN
    # Observability settings
    metrics_enabled: bool = True
    telemetry_enabled: bool = False  # Opt-in by default
    crash_reporting_enabled: bool = False  # Opt-in by default
    # Matching behavior
    fail_on_ambiguous_matches: bool = True  # Fail fast by default for production
    
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
            required_column=data.get('required_column', DEFAULT_SERIAL_NUMBERS_COLUMN),
            metrics_enabled=data.get('metrics_enabled', True),
            telemetry_enabled=data.get('telemetry_enabled', False),
            crash_reporting_enabled=data.get('crash_reporting_enabled', False),
            fail_on_ambiguous_matches=data.get('fail_on_ambiguous_matches', True)
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
    
    def merge(self, other: 'AppConfig') -> 'AppConfig':
        """
        Merge another config into this one (other takes precedence for non-None values).
        
        Args:
            other: Config to merge in
            
        Returns:
            New merged config
        """
        return AppConfig(
            input_file=other.input_file if other.input_file else self.input_file,
            pdf_dir=other.pdf_dir if other.pdf_dir else self.pdf_dir,
            output_dir=other.output_dir if other.output_dir else self.output_dir,
            required_column=other.required_column if other.required_column != DEFAULT_SERIAL_NUMBERS_COLUMN or self.required_column == DEFAULT_SERIAL_NUMBERS_COLUMN else self.required_column,
            metrics_enabled=other.metrics_enabled if hasattr(other, 'metrics_enabled') else self.metrics_enabled,
            telemetry_enabled=other.telemetry_enabled if hasattr(other, 'telemetry_enabled') else self.telemetry_enabled,
            crash_reporting_enabled=other.crash_reporting_enabled if hasattr(other, 'crash_reporting_enabled') else self.crash_reporting_enabled,
            fail_on_ambiguous_matches=other.fail_on_ambiguous_matches if hasattr(other, 'fail_on_ambiguous_matches') else self.fail_on_ambiguous_matches
        )


def get_config_path() -> Path:
    """
    Get the path to the user configuration file.
    
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


def find_project_preset(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find per-project preset file (.pdf_merger_config.json) by walking up from start_path.
    
    Args:
        start_path: Starting path to search from (defaults to current working directory)
        
    Returns:
        Path to preset file if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = Path(start_path).resolve()
    
    # Walk up the directory tree
    while current != current.parent:
        preset_path = current / PROJECT_PRESET_FILENAME
        if preset_path.exists() and preset_path.is_file():
            logger.debug(f"Found project preset at {preset_path}")
            return preset_path
        current = current.parent
    
    return None


def load_project_preset(start_path: Optional[Path] = None) -> Optional[AppConfig]:
    """
    Load per-project preset configuration.
    
    Args:
        start_path: Starting path to search from
        
    Returns:
        AppConfig from preset if found, None otherwise
    """
    preset_path = find_project_preset(start_path)
    if not preset_path:
        return None
    
    try:
        with open(preset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = AppConfig.from_dict(data)
        logger.info(f"Loaded project preset from {preset_path}")
        return config
    except Exception as e:
        logger.warning(f"Error loading project preset from {preset_path}: {e}")
        return None


def load_user_config() -> AppConfig:
    """
    Load configuration from user config file.
    
    Returns:
        AppConfig object (default if file doesn't exist)
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        logger.debug(f"User config file not found at {config_path}, using defaults")
        return AppConfig()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Validate config
        validated_data = ConfigSchema.validate_config(data)
        config = AppConfig.from_dict(validated_data)
        logger.info(f"Loaded user config from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Error loading user config from {config_path}: {e}, using defaults")
        return AppConfig()


def load_env_config() -> AppConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        AppConfig from environment variables
    """
    config_data = {}
    
    if ENV_INPUT_FILE in os.environ:
        config_data['input_file'] = os.environ[ENV_INPUT_FILE]
    
    if ENV_SOURCE_DIR in os.environ:
        config_data['pdf_dir'] = os.environ[ENV_SOURCE_DIR]
    
    if ENV_OUTPUT_DIR in os.environ:
        config_data['output_dir'] = os.environ[ENV_OUTPUT_DIR]
    
    if ENV_COLUMN in os.environ:
        config_data['required_column'] = os.environ[ENV_COLUMN]
    
    if config_data:
        logger.debug("Loaded configuration from environment variables")
        # Validate config
        validated_data = ConfigSchema.validate_config(config_data)
        return AppConfig.from_dict(validated_data)
    
    return AppConfig()


def load_config(
    start_path: Optional[Path] = None
) -> AppConfig:
    """
    Load configuration with full precedence support.
    
    Precedence order (highest to lowest):
    1. Environment variables
    2. User config file
    3. Per-project preset
    4. Defaults
    
    Args:
        start_path: Starting path for project preset search
        
    Returns:
        AppConfig with merged configuration
    """
    # Start with defaults
    config = AppConfig()
    
    # 3. Load per-project preset (lowest priority)
    project_preset = load_project_preset(start_path)
    if project_preset:
        config = config.merge(project_preset)
    
    # 2. Load user config file
    user_config = load_user_config()
    config = config.merge(user_config)
    
    # 1. Apply environment variables (highest priority)
    env_config = load_env_config()
    config = config.merge(env_config)
    
    return config


def save_config(config: AppConfig) -> bool:
    """
    Save configuration to user config file.
    
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
