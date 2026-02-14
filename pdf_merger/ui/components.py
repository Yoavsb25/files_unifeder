"""
UI components for PDF Merger application.
"""

import customtkinter as ctk
from typing import Any, Callable, Optional, Union

from .. import APP_VERSION, APP_NAME
from .display_enums import StatusColor
from .theme import (
    CARD_BG,
    CARD_BORDER,
    CORNER_RADIUS,
    CARD_PADDING,
    INPUT_RADIUS,
    INPUT_BACKGROUND,
    INPUT_CONTAINER_BG,
    PRIMARY_BLUE,
    FONT_LABEL_SIZE,
    FONT_SECTION_SIZE,
    FONT_HELPER_SIZE,
    FONT_MONO_SIZE,
    FONT_SUMMARY_NUMBER,
    INPUT_BG,
    LOG_BG,
    LABEL_INPUT_SPACING,
    METRIC_CARD_BG,
    METRIC_CARD_PADDING,
    SECTION_SPACING,
    SUMMARY_CARD_SPACING,
    STEP_SYMBOLS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    GREEN_SUCCESS,
    RED_ERROR,
    YELLOW_WARNING,
    BLUE_INFO,
)


class LogHandler:
    """Custom log handler that writes to GUI text widget.
    Buffers messages and flushes to the widget on flush() to batch updates and reduce UI flicker.
    """

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = []
    
    def write(self, message: str):
        """Write log message to buffer."""
        if message.strip():
            self.buffer.append(message.strip())
    
    def flush(self):
        """Flush buffer to text widget."""
        if self.buffer:
            text = "\n".join(self.buffer)
            self.text_widget.insert("end", text + "\n")
            self.text_widget.see("end")
            self.buffer.clear()


def bind_focus_highlight(
    entry: ctk.CTkEntry,
    border_color_focus: str = PRIMARY_BLUE,
    border_color_default: str = CARD_BORDER,
    on_focus_out: Optional[Callable[[], None]] = None,
) -> None:
    """Bind focus in/out: border_color_focus on focus, on FocusOut call on_focus_out or set border to border_color_default."""
    entry.bind("<FocusIn>", lambda e: entry.configure(border_color=border_color_focus))
    if on_focus_out is not None:
        entry.bind("<FocusOut>", lambda e: on_focus_out())
    else:
        entry.bind("<FocusOut>", lambda e: entry.configure(border_color=border_color_default))


def _mono_font():
    """Monospace font for path inputs (cross-platform)."""
    return ctk.CTkFont(family="Courier New", size=FONT_MONO_SIZE)


class SetupCard(ctk.CTkFrame):
    """Step-based setup card - flat styling, input-style container."""

    def __init__(
        self,
        parent,
        step_number: int,
        title: str,
        helper_text: str,
        button_text: str = "Browse...",
        on_select: Optional[Callable] = None,
        extra_row: Optional[Any] = None,
    ):
        super().__init__(
            parent,
            fg_color=CARD_BG,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.on_select = on_select
        self._error_message: Optional[str] = None

        # Header: step badge + title (12px below label to input)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(CARD_PADDING, LABEL_INPUT_SPACING), padx=CARD_PADDING)

        step_label = ctk.CTkLabel(
            header_frame,
            text=STEP_SYMBOLS[step_number - 1] if 1 <= step_number <= 3 else str(step_number),
            font=ctk.CTkFont(size=FONT_SECTION_SIZE, weight="bold"),
            width=28,
        )
        step_label.pack(side="left", padx=(0, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=FONT_LABEL_SIZE, weight="bold"),
        )
        title_label.pack(side="left")

        # Input row: path entry (input-style) + browse button, height 40px
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=CARD_PADDING, pady=(0, LABEL_INPUT_SPACING))

        self.path_entry = ctk.CTkEntry(
            input_frame,
            height=40,
            font=_mono_font(),
            placeholder_text="No selection",
            fg_color=INPUT_BACKGROUND,
            corner_radius=INPUT_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        bind_focus_highlight(self.path_entry, on_focus_out=self._on_entry_focus_out)

        # Secondary-style browse button, height matches input
        self.browse_button = ctk.CTkButton(
            input_frame,
            text=button_text,
            command=self._on_browse_clicked,
            width=100,
            height=40,
            fg_color=INPUT_BACKGROUND,
            hover_color=CARD_BORDER,
            corner_radius=INPUT_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
            cursor="hand2",
        )
        self.browse_button.pack(side="right")

        # Optional extra row (e.g. Serial numbers column) - 12px below input
        if extra_row is not None:
            extra_row.pack(fill="x", padx=CARD_PADDING, pady=(0, LABEL_INPUT_SPACING))

        # Helper text (12px muted)
        self.helper_label = ctk.CTkLabel(
            self,
            text=f"ⓘ {helper_text}",
            font=ctk.CTkFont(size=FONT_HELPER_SIZE),
            text_color=TEXT_SECONDARY,
        )
        self.helper_label.pack(anchor="w", padx=CARD_PADDING, pady=(0, 4))

        # Error message (hidden by default)
        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=FONT_HELPER_SIZE),
            text_color=RED_ERROR,
        )
        self.error_label.pack(anchor="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))

    def _on_entry_focus_out(self):
        """Restore default border when focus lost (unless error state)."""
        if not self._error_message:
            try:
                self.path_entry.configure(border_color=CARD_BORDER)
            except Exception:
                pass

    def _on_browse_clicked(self):
        if self.on_select:
            self.on_select()

    def set_path(self, path: str):
        """Update the displayed path."""
        self.path_entry.delete(0, "end")
        if path:
            self.path_entry.insert(0, path)

    def get_path(self) -> str:
        return self.path_entry.get() or ""

    def set_error(self, message: str):
        """Show inline error state."""
        self._error_message = message
        self.path_entry.configure(border_color=RED_ERROR, border_width=2)
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))

    def has_error(self) -> bool:
        """Return True if the selector has an active error state."""
        return self._error_message is not None

    def clear_error(self):
        """Clear error state."""
        self._error_message = None
        self.path_entry.configure(border_width=1, border_color=CARD_BORDER)
        self.error_label.configure(text="")
        self.error_label.pack_forget()




class LicenseFrame(ctk.CTkFrame):
    """License status display frame - pill-style badge."""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Pill-style badge container
        badge_frame = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=20,
            height=36,
        )
        badge_frame.pack(fill="x")
        badge_frame.pack_propagate(False)
        
        self.license_label = ctk.CTkLabel(
            badge_frame,
            text="Checking license...",
            font=ctk.CTkFont(size=12),
        )
        self.license_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def update_status(self, text: str, color: Union[str, StatusColor] = StatusColor.WHITE):
        """Update license status display.
        
        Args:
            text: Status text to display
            color: Color string or StatusColor enum (defaults to white)
        """
        color_value = color.value if isinstance(color, StatusColor) else color
        self.license_label.configure(text=text, text_color=color_value)


class LogArea(ctk.CTkFrame):
    """Log/output display area - collapsible, with colored output."""

    TAG_ERROR = "error"
    TAG_SUCCESS = "success"
    TAG_INFO = "info"
    TAG_WARNING = "warning"

    EMOJI_ERROR = "✗ "
    EMOJI_SUCCESS = "✓ "
    EMOJI_INFO = "ⓘ "
    EMOJI_WARNING = "⚠ "

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._expanded = False

        # Collapsible header (clickable)
        self.header_btn = ctk.CTkButton(
            self,
            text="Detailed Log  ▶",
            font=ctk.CTkFont(size=FONT_LABEL_SIZE, weight="bold"),
            fg_color="transparent",
            hover_color=CARD_BG,
            anchor="w",
            command=self._toggle,
            cursor="hand2",
        )
        self.header_btn.pack(fill="x", padx=0, pady=(0, 4))

        # Content frame (initially hidden - collapsed by default)
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=LOG_BG,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        # Text widget - monospace, scrollable (has built-in scrollbar)
        self.log_text = ctk.CTkTextbox(
            self.content_frame,
            font=ctk.CTkFont(size=FONT_MONO_SIZE),
            wrap="word",
            height=300,
            fg_color=LOG_BG,
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Configure tags for colored output (theme semantic colors)
        self.log_text.tag_config(self.TAG_ERROR, foreground=RED_ERROR)
        self.log_text.tag_config(self.TAG_SUCCESS, foreground=GREEN_SUCCESS)
        self.log_text.tag_config(self.TAG_INFO, foreground=TEXT_SECONDARY)
        self.log_text.tag_config(self.TAG_WARNING, foreground=YELLOW_WARNING)

    def is_expanded(self) -> bool:
        """Return True if the detailed log area is expanded (visible)."""
        return self._expanded

    def toggle_detail(self) -> bool:
        """Toggle collapsed/expanded state. Returns the new expanded state."""
        self._expanded = not self._expanded
        if self._expanded:
            self.content_frame.pack(fill="both", expand=True, padx=0, pady=(0, 8))
            self.header_btn.configure(text="Detailed Log  ▼")
        else:
            self.content_frame.pack_forget()
            self.header_btn.configure(text="Detailed Log  ▶")
        return self._expanded

    def _toggle(self):
        """Internal: toggle collapsed/expanded (used by header button command)."""
        self.toggle_detail()

    def log_warning(self, message: str):
        """Add warning message with yellow color."""
        self._log_with_tag(message, self.TAG_WARNING, self.EMOJI_WARNING)

    def _log_with_tag(self, message: str, tag: str, emoji: str):
        """Add message with color tag and emoji."""
        text = emoji + message + "\n"
        self.log_text.insert("end", text, tag)
        self.log_text.see("end")

    def log(self, message: str):
        """Add plain message to log area."""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def log_info(self, message: str):
        """Add info message with blue color."""
        self._log_with_tag(message, self.TAG_INFO, self.EMOJI_INFO)

    def log_success(self, message: str):
        """Add success message with green color."""
        self._log_with_tag(message, self.TAG_SUCCESS, self.EMOJI_SUCCESS)

    def log_error(self, message: str):
        """Add error message with red color."""
        self._log_with_tag(message, self.TAG_ERROR, self.EMOJI_ERROR)

    def clear(self):
        """Clear the log area."""
        self.log_text.delete("1.0", "end")

    def winfo_ismapped(self):
        """Return whether the log area is visible (for toggle logic)."""
        return self.content_frame.winfo_ismapped()


class ResultsFrame(ctk.CTkFrame):
    """Results section - single card container, flat styling, accurate labels."""

    def __init__(self, parent, on_open_output: Optional[Callable] = None, on_toggle_log: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.on_open_output = on_open_output
        self.on_toggle_log = on_toggle_log
        self._output_dir: Optional[str] = None

        # Single results card container
        results_card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        results_card.pack(fill="x")

        inner = ctk.CTkFrame(results_card, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PADDING, pady=CARD_PADDING)

        # Title
        header = ctk.CTkLabel(
            inner,
            text="Results",
            font=ctk.CTkFont(size=FONT_SECTION_SIZE, weight="bold"),
        )
        header.pack(anchor="w", pady=(0, 8))

        # Human summary line
        self.summary_label = ctk.CTkLabel(
            inner,
            text="Merge completed successfully",
            font=ctk.CTkFont(size=FONT_HELPER_SIZE),
            text_color=TEXT_SECONDARY,
        )
        self.summary_label.pack(anchor="w", pady=(0, 16))

        # Metric mini-cards row
        cards_frame = ctk.CTkFrame(inner, fg_color="transparent")
        cards_frame.pack(fill="x")

        # Rows Analyzed (TEXT_PRIMARY)
        self.rows_card = self._make_summary_card(cards_frame, "0", "Rows Analyzed", TEXT_PRIMARY)
        self.rows_card.pack(side="left", fill="x", expand=True, padx=(0, SUMMARY_CARD_SPACING))

        # PDFs Created (SUCCESS_GREEN)
        self.pdfs_card = self._make_summary_card(cards_frame, "0", "PDFs Created", GREEN_SUCCESS)
        self.pdfs_card.pack(side="left", fill="x", expand=True, padx=(0, SUMMARY_CARD_SPACING))

        # Skipped (WARNING_YELLOW)
        self.skipped_card = self._make_summary_card(cards_frame, "0", "Skipped", YELLOW_WARNING)
        self.skipped_card.pack(side="left", fill="x", expand=True, padx=(0, SUMMARY_CARD_SPACING))

        # Failed (ERROR_RED)
        self.failed_card = self._make_summary_card(cards_frame, "0", "Failed", RED_ERROR)
        self.failed_card.pack(side="left", fill="x", expand=True)

        # Action buttons
        buttons_frame = ctk.CTkFrame(inner, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(16, 0))

        self.view_log_btn = ctk.CTkButton(
            buttons_frame,
            text="View Detailed Log",
            command=self._on_toggle_log_clicked,
            fg_color=INPUT_CONTAINER_BG,
            hover_color=CARD_BORDER,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
            width=140,
            cursor="hand2",
        )
        self.view_log_btn.pack(side="left", padx=(0, 8))

        self.open_folder_btn = ctk.CTkButton(
            buttons_frame,
            text="Open Output Folder",
            command=self._on_open_output_clicked,
            fg_color=INPUT_CONTAINER_BG,
            hover_color=CARD_BORDER,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
            width=160,
            cursor="hand2",
        )
        self.open_folder_btn.pack(side="left")

    def _make_summary_card(self, parent, value: str, label: str, color: str):
        """Create a metric mini-card: METRIC_CARD_BG, 16px padding, center-aligned, 28-32px number."""
        card = ctk.CTkFrame(
            parent,
            fg_color=METRIC_CARD_BG,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=METRIC_CARD_PADDING, pady=METRIC_CARD_PADDING)
        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=FONT_SUMMARY_NUMBER, weight="bold"),
            text_color=color,
        )
        val_lbl.pack(anchor="center")
        lbl = ctk.CTkLabel(
            inner,
            text=label,
            font=ctk.CTkFont(size=FONT_HELPER_SIZE),
            text_color=TEXT_SECONDARY,
        )
        lbl.pack(anchor="center")
        card.value_label = val_lbl
        return card

    def update_results(
        self,
        rows_analyzed: int,
        pdfs_created: int,
        skipped: int,
        failed: int,
        output_dir: Optional[str] = None,
    ):
        """Update summary cards and human summary line."""
        self.rows_card.value_label.configure(text=str(rows_analyzed))
        self.pdfs_card.value_label.configure(text=str(pdfs_created))
        self.skipped_card.value_label.configure(text=str(skipped))
        self.failed_card.value_label.configure(text=str(failed))
        self.summary_label.configure(
            text="Merge completed with errors" if failed > 0 else "Merge completed successfully"
        )
        self._output_dir = output_dir
        self.open_folder_btn.configure(
            state="normal" if (pdfs_created > 0 and output_dir) else "disabled"
        )

    def _on_open_output_clicked(self):
        if self.on_open_output and self._output_dir:
            self.on_open_output(self._output_dir)

    def _on_toggle_log_clicked(self):
        if self.on_toggle_log:
            self.on_toggle_log()

    def show(self, before=None):
        """Show the results section. If before is set, pack before that widget."""
        kwargs = {"fill": "x", "pady": (0, SECTION_SPACING)}
        if before is not None:
            kwargs["before"] = before
        self.pack(**kwargs)

    def hide(self):
        """Hide the results section."""
        self.pack_forget()


class Footer(ctk.CTkFrame):
    """Application footer - version only, visually subtle."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        version_label = ctk.CTkLabel(
            self,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=ctk.CTkFont(size=FONT_HELPER_SIZE),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        version_label.pack(side="left", padx=10, pady=5)

    def update_status(self, text: str, color: Union[str, StatusColor] = StatusColor.WHITE):
        """No-op for backward compatibility - status removed per spec."""
        pass
