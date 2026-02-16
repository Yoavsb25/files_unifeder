"""
Single place for applying a selected path to app state, selector, config, and UI.
App holds the controller and delegates path application here.
"""

from pathlib import Path
from typing import Any, Callable, Dict

# AppConfig type for type hints; avoid circular import by using string or Any
# Callers pass get_config/set_config that operate on their AppConfig.


class PathController:
    """
    Applies a selected path to app state, selector, config, and UI.
    Dependencies are injected at construction so the flow is testable without Tk.
    """

    def __init__(
        self,
        get_config: Callable[[], Any],
        set_config: Callable[[str, Path, Any], None],
        save_config_fn: Callable[[Any], None],
        log_info_fn: Callable[[str], None],
        update_ui_state_fn: Callable[[], None],
    ):
        self._get_config = get_config
        self._set_config = set_config
        self._save_config_fn = save_config_fn
        self._log_info_fn = log_info_fn
        self._update_ui_state_fn = update_ui_state_fn

    def apply_path(
        self,
        path: Path,
        path_attr: str,
        selector: Any,
        config_override: Dict[str, str],
        log_message: str,
    ) -> None:
        """Set path on app, update selector, merge config, save, log, and refresh UI."""
        current = self._get_config()
        config = current.merge(type(current)(**config_override))
        self._set_config(path_attr, path, config)
        selector.set_path(str(path))
        selector.clear_error()
        self._save_config_fn(config)
        self._log_info_fn(log_message)
        self._update_ui_state_fn()
