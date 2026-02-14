"""
UI components for PDF Merger application.
"""

import customtkinter as ctk
from typing import Callable, Optional, Union

from .. import APP_VERSION, APP_NAME
from ..core.enums import StatusColor


class LogHandler:
    """Custom log handler that writes to GUI text widget."""
    
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


class FileSelector(ctk.CTkFrame):
    """Reusable file/directory selector component."""
    
    def __init__(
        self,
        parent,
        label_text: str,
        button_text: str = "Browse...",
        on_select: Optional[Callable] = None
    ):
        super().__init__(parent)
        
        self.on_select = on_select
        
        # Label
        ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        # Button frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x")
        
        # File/directory label
        self.path_label = ctk.CTkLabel(
            button_frame,
            text="No selection",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.path_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Browse button
        self.browse_button = ctk.CTkButton(
            button_frame,
            text=button_text,
            command=self._on_browse_clicked,
            width=100
        )
        self.browse_button.pack(side="right")
    
    def _on_browse_clicked(self):
        """Handle browse button click."""
        if self.on_select:
            self.on_select()
    
    def set_path(self, path: str):
        """Update the displayed path."""
        self.path_label.configure(text=path)
    
    def get_path(self) -> str:
        """Get the currently displayed path."""
        return self.path_label.cget("text")


class LicenseFrame(ctk.CTkFrame):
    """License status display frame."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.license_label = ctk.CTkLabel(
            self,
            text="Checking license...",
            font=ctk.CTkFont(size=12)
        )
        self.license_label.pack(pady=10)
    
    def update_status(self, text: str, color: Union[str, StatusColor] = StatusColor.WHITE):
        """Update license status display.
        
        Args:
            text: Status text to display
            color: Color string or StatusColor enum (defaults to white)
        """
        color_value = color.value if isinstance(color, StatusColor) else color
        self.license_label.configure(text=text, text_color=color_value)


class LogArea(ctk.CTkFrame):
    """Log/output display area with colored output and emojis."""

    # Tag names for colored text
    TAG_ERROR = "error"
    TAG_SUCCESS = "success"
    TAG_INFO = "info"

    # Emojis for visual clarity
    EMOJI_ERROR = "❌ "
    EMOJI_SUCCESS = "✅ "
    EMOJI_INFO = "📋 "

    def __init__(self, parent):
        super().__init__(parent)

        # Label
        ctk.CTkLabel(
            self,
            text="Output Log:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Text widget
        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=11),
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure tags for colored output
        self.log_text.tag_config(self.TAG_ERROR, foreground="#e74c3c")  # red
        self.log_text.tag_config(self.TAG_SUCCESS, foreground="#27ae60")  # green
        self.log_text.tag_config(self.TAG_INFO, foreground="#3498db")  # blue

    def _log_with_tag(self, message: str, tag: str, emoji: str):
        """Add message with color tag and emoji."""
        text = emoji + message + "\n"
        self.log_text.insert("end", text, tag)
        self.log_text.see("end")

    def log(self, message: str):
        """Add plain message to log area (backward compatible)."""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def log_info(self, message: str):
        """Add info message with blue color and info emoji."""
        self._log_with_tag(message, self.TAG_INFO, self.EMOJI_INFO)

    def log_success(self, message: str):
        """Add success message with green color and checkmark emoji."""
        self._log_with_tag(message, self.TAG_SUCCESS, self.EMOJI_SUCCESS)

    def log_error(self, message: str):
        """Add error message with red color and error emoji."""
        self._log_with_tag(message, self.TAG_ERROR, self.EMOJI_ERROR)

    def clear(self):
        """Clear the log area."""
        self.log_text.delete("1.0", "end")


class Footer(ctk.CTkFrame):
    """Application footer with version and status."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Version label
        version_label = ctk.CTkLabel(
            self,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        version_label.pack(side="left", padx=10, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=10),
            anchor="e"
        )
        self.status_label.pack(side="right", padx=10, pady=5)
    
    def update_status(self, text: str, color: Union[str, StatusColor] = StatusColor.WHITE):
        """Update status display.
        
        Args:
            text: Status text to display
            color: Color string or StatusColor enum (defaults to white)
        """
        color_value = color.value if isinstance(color, StatusColor) else color
        self.status_label.configure(text=text, text_color=color_value)
