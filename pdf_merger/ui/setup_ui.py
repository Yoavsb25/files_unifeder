"""
Build header (title, license, column row) and setup cards for the main app.
Extracted so app.py stays under ~350 lines and composition is clear.
"""

import customtkinter as ctk
from typing import Any, Callable, Tuple

from ..core.constants import Constants
from .components import SetupCard, LicenseFrame, bind_focus_highlight
from .theme import (
    COLUMN_ENTRY_WIDTH,
    CORNER_RADIUS,
    SECTION_SPACING,
    CARD_SPACING,
    APP_BACKGROUND,
    CARD_BORDER,
    FONT_TITLE_SIZE,
    FONT_LABEL_SIZE,
    FONT_MONO_SIZE,
    INPUT_BACKGROUND,
)


def build_header(
    main_frame: Any,
    app_name: str,
) -> Tuple[Any, Any, Any]:
    """
    Build title, license frame, and serial numbers column row.
    Returns (license_frame, column_frame, column_entry).
    """
    title_label = ctk.CTkLabel(
        main_frame,
        text=app_name,
        font=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold"),
    )
    title_label.pack(pady=(0, SECTION_SPACING))
    license_frame = LicenseFrame(main_frame)
    license_frame.pack(fill="x", pady=(0, SECTION_SPACING))
    column_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    ctk.CTkLabel(
        column_frame,
        text="Serial numbers column:",
        font=ctk.CTkFont(size=FONT_LABEL_SIZE, weight="bold"),
    ).pack(anchor="w", side="left", padx=(0, 8))
    column_entry = ctk.CTkEntry(
        column_frame,
        placeholder_text=Constants.EXAMPLE_SERIAL_COLUMN_PLACEHOLDER,
        font=ctk.CTkFont(family="Courier New", size=FONT_MONO_SIZE),
        width=COLUMN_ENTRY_WIDTH,
        height=40,
        fg_color=INPUT_BACKGROUND,
        border_width=1,
        border_color=CARD_BORDER,
    )
    column_entry.pack(side="left")
    bind_focus_highlight(column_entry)
    return license_frame, column_frame, column_entry


def build_setup_cards(
    main_frame: Any,
    column_frame: Any,
    on_select_input: Callable[[], None],
    on_select_pdf_dir: Callable[[], None],
    on_select_output: Callable[[], None],
) -> Tuple[Any, Any, Any]:
    """
    Build the three setup cards (Instructions File, Source Directory, Output Directory).
    Returns (input_file_selector, pdf_dir_selector, output_dir_selector).
    """
    input_file_selector = SetupCard(
        main_frame,
        step_number=1,
        title="Instructions File",
        helper_text=Constants.EXAMPLE_SERIAL_COLUMN_HELPER,
        on_select=on_select_input,
        extra_row=column_frame,
    )
    input_file_selector.pack(fill="x", pady=(0, CARD_SPACING))
    pdf_dir_selector = SetupCard(
        main_frame,
        step_number=2,
        title="Source Directory",
        helper_text="All referenced PDFs & Excel files must live here",
        on_select=on_select_pdf_dir,
    )
    pdf_dir_selector.pack(fill="x", pady=(0, CARD_SPACING))
    output_dir_selector = SetupCard(
        main_frame,
        step_number=3,
        title="Output Directory",
        helper_text="Merged PDFs will be saved here",
        on_select=on_select_output,
    )
    output_dir_selector.pack(fill="x", pady=(0, SECTION_SPACING))
    return input_file_selector, pdf_dir_selector, output_dir_selector
