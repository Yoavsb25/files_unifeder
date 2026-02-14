"""
Apply application config to UI fields.
Pure helper for loading config (paths, column name) into selectors and path attributes;
used by the main app so config-into-UI logic is testable and keeps app.py short.
"""

from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from ..utils.exceptions import PDFMergerError


def load_config_into_ui(
    config: Any,
    column_entry: Any,
    input_selector: Any,
    pdf_dir_selector: Any,
    output_selector: Any,
    set_path_attr: Callable[[str, Path], None],
    log_info: Callable[[str], None],
    log_warning: Callable[[str], None],
    on_update_state: Callable[[], None],
) -> None:
    """
    Build path applyments and load config into UI (column + paths). Single entry point for app.
    """
    from ..utils.validators import validate_file, validate_folder

    def validate_input(p: Path) -> None:
        validate_file(p, required_column=config.required_column)

    def validate_source(p: Path) -> None:
        validate_folder(p, "Source")

    def validate_output(p: Path) -> None:
        p.mkdir(parents=True, exist_ok=True)

    path_applyments: List[Tuple[Optional[str], str, Any, Callable[[Path], None], str]] = [
        (config.input_file, "input_file_path", input_selector, validate_input, "input file"),
        (config.pdf_dir, "pdf_dir_path", pdf_dir_selector, validate_source, "source directory"),
        (config.output_dir, "output_dir_path", output_selector, validate_output, "output directory"),
    ]
    apply_config_to_ui(
        config,
        column_entry=column_entry,
        path_applyments=path_applyments,
        set_path_attr=set_path_attr,
        log_info=log_info,
        log_warning=log_warning,
        on_update_state=on_update_state,
    )


def apply_config_to_ui(
    config: Any,
    *,
    column_entry: Any,
    path_applyments: List[Tuple[Optional[str], str, Any, Callable[[Path], None], str]],
    set_path_attr: Callable[[str, Path], None],
    log_info: Callable[[str], None],
    log_warning: Callable[[str], None],
    on_update_state: Callable[[], None],
) -> None:
    """
    Load configuration into UI: set column name and apply each path to selector and path attribute.

    For each (path_str, path_attr, selector, validator, log_label) in path_applyments,
    if path_str is set, validates the path, sets the path attribute via set_path_attr,
    updates the selector display, and logs. On validation or path error, logs a warning
    and continues. Finally calls on_update_state().

    Args:
        config: AppConfig-like with required_column and path fields.
        column_entry: Entry widget for column name; will have config.required_column inserted at 0.
        path_applyments: List of (path_str, path_attr, selector, validator, log_label).
        set_path_attr: Called as set_path_attr(path_attr, path) to store the path on the app.
        log_info: Info logger (e.g. logger.info).
        log_warning: Warning logger (e.g. logger.warning).
        on_update_state: Called once after applying all paths (e.g. app._update_ui_state).
    """
    column_entry.insert(0, config.required_column)
    for path_str, path_attr, selector, validator, log_label in path_applyments:
        if not path_str:
            continue
        try:
            path = Path(path_str)
            validator(path)
            set_path_attr(path_attr, path)
            selector.set_path(str(path))
            log_info(f"Loaded {log_label} from config: {path}")
        except (OSError, ValueError, PDFMergerError) as e:
            log_warning(f"Could not load {log_label} from config: {e}")
    on_update_state()
