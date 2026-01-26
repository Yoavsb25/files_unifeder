"""
License-related UI logic.
"""

from typing import Optional

import customtkinter as ctk

from ..licensing import LicenseManager, LicenseStatus
from ..core.enums import LicenseColor, WarningLevel

# Constants for backward compatibility and convenience
GREEN_COLOR = LicenseColor.GREEN.value
RED_COLOR = LicenseColor.RED.value
ORANGE_COLOR = LicenseColor.ORANGE.value
YELLOW_COLOR = LicenseColor.YELLOW.value

VALID_LICENSE = "✓ License valid"
EXPIRED_LICENSE = "⚠ License expired - Merge functionality disabled"

def match_color_to_display_text(
    color: str,
    company_name: str,
    expires: str,
    warning_msg: Optional[str] = None,
    error_msg: Optional[str] = None
) -> str:
    """
    Generate license display text based on color and context.
    
    Args:
        color: Color string (LicenseColor enum value or string)
        company_name: Licensed company name
        expires: License expiration date
        warning_msg: Optional warning message (for YELLOW/RED warnings)
        error_msg: Optional error message (for RED errors)
    
    Returns:
        Formatted display text for the license status
    """
    if color == GREEN_COLOR or color == LicenseColor.GREEN.value:
        return f"✓ Licensed to: {company_name} (Expires: {expires})"
    
    if color == ORANGE_COLOR or color == LicenseColor.ORANGE.value:
        return EXPIRED_LICENSE
    
    if color == YELLOW_COLOR or color == LicenseColor.YELLOW.value:
        if warning_msg:
            return f"✓ Licensed to: {company_name} - {warning_msg}"
        return f"✓ Licensed to: {company_name} (Expires: {expires})"
    
    if color == RED_COLOR or color == LicenseColor.RED.value:
        # RED can represent critical warnings OR errors
        # Priority: warning_msg (critical warning) > error_msg (actual error)
        if warning_msg:
            return f"✓ Licensed to: {company_name} - {warning_msg}"
        if error_msg:
            return f"✗ {error_msg}"
        return "Unknown license status"
    
    return "Unknown license status"

def match_color_to_warning_level(warning_level: WarningLevel) -> str:
    """
    Match color to warning level.
    
    Args:
        warning_level: WarningLevel enum value
    
    Returns:
        Color string value for the warning level
    """
    # Map warning level enum to colors
    warning_to_color = {
        WarningLevel.EXPIRED: LicenseColor.RED.value,
        WarningLevel.CRITICAL: LicenseColor.RED.value,
        WarningLevel.WARNING: LicenseColor.ORANGE.value,
        WarningLevel.INFO: LicenseColor.YELLOW.value,
    }
    return warning_to_color.get(warning_level, LicenseColor.YELLOW.value)

def update_license_display(license_manager: LicenseManager, license_label) -> bool:
    """
    Update license status display and return whether license is valid.
    
    Args:
        license_manager: The license manager instance
        license_label: The label widget to update
        
    Returns:
        True if license is valid, False otherwise
    """
    status = license_manager.get_license_status()
    license_valid = (status == LicenseStatus.VALID)

    if license_valid:
        info = license_manager.get_license_info()
        if not info:
            # No license info available - show simple valid message
            license_label.configure(
                text=VALID_LICENSE,
                text_color=GREEN_COLOR,
                font=ctk.CTkFont(size=18, weight="bold")
            )
        else:
            warning_msg = license_manager.get_expiry_warning_message()
            warning_level_str = info.get("expiry_warning_level", "info")
            # Convert string to WarningLevel enum if needed
            if isinstance(warning_level_str, str):
                try:
                    warning_level = WarningLevel(warning_level_str)
                except ValueError:
                    warning_level = WarningLevel.INFO
            else:
                warning_level = warning_level_str if isinstance(warning_level_str, WarningLevel) else WarningLevel.INFO
            company_name = info.get("company", "Unknown")
            expires = info.get("expires", "Unknown")
            error_msg = ""

            text_color = GREEN_COLOR if not warning_msg else match_color_to_warning_level(warning_level)
            display_text = match_color_to_display_text(
                text_color, company_name, expires, warning_msg, error_msg
            )

            license_label.configure(
                text=display_text,
                text_color=text_color,
                font=ctk.CTkFont(size=18, weight="bold")
            )
    elif status == LicenseStatus.EXPIRED:
        license_label.configure(
            text=EXPIRED_LICENSE,
            text_color=ORANGE_COLOR,
            font=ctk.CTkFont(size=18, weight="bold")
        )
    else:
        error_msg = license_manager.get_license_error_message(status)
        license_label.configure(
            text=f"✗ {error_msg}",
            text_color=RED_COLOR,
            font=ctk.CTkFont(size=18, weight="bold")
        )

    return license_valid
