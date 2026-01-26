"""
Configuration module.
Handles application configuration management.
"""

# Re-export for backward compatibility
from .config_manager import (
    AppConfig,
    get_config_path,
    load_config,
    save_config,
    find_project_preset,
    load_project_preset,
    load_user_config,
    load_env_config,
    ENV_INPUT_FILE,
    ENV_SOURCE_DIR,
    ENV_OUTPUT_DIR,
    ENV_COLUMN,
    PROJECT_PRESET_FILENAME,
)

__all__ = [
    'AppConfig',
    'get_config_path',
    'load_config',
    'save_config',
    'find_project_preset',
    'load_project_preset',
    'load_user_config',
    'load_env_config',
    'ENV_INPUT_FILE',
    'ENV_SOURCE_DIR',
    'ENV_OUTPUT_DIR',
    'ENV_COLUMN',
    'PROJECT_PRESET_FILENAME',
]
