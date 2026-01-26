"""
License manager.
Main license validation and verification logic with enhanced UX.
"""

import socket
from pathlib import Path
from typing import Optional

from .license_model import License
from .license_signer import get_embedded_public_key, verify_license_signature
from ..enums import LicenseStatus, WarningLevel
from ..logger import get_logger

logger = get_logger("licensing.manager")


class LicenseManager:
    """Manages license validation and verification with enhanced UX."""
    
    def __init__(self, app_version: str = "1.0.0", clock_skew_tolerance_minutes: int = 5):
        """
        Initialize license manager.
        
        Args:
            app_version: Current application version
            clock_skew_tolerance_minutes: Tolerance for clock skew in minutes (default: 5)
        """
        self.app_version = app_version
        self.clock_skew_tolerance_minutes = clock_skew_tolerance_minutes
        self._cached_license: Optional[License] = None
        self._cached_status: Optional[LicenseStatus] = None
        self._last_license_mtime: Optional[float] = None
    
    def get_license_path(self) -> Path:
        """
        Get the path to the license file.
        
        Returns:
            Path to license.json (checks app directory first, then user home)
        """
        # Try app directory first (for packaged app)
        app_dir = Path(__file__).parent.parent.parent
        app_license = app_dir / 'license.json'
        if app_license.exists():
            return app_license
        
        # Fall back to user home directory
        home_dir = Path.home()
        license_dir = home_dir / '.pdf_merger'
        return license_dir / 'license.json'
    
    def load_license(self, force_refresh: bool = False) -> Optional[License]:
        """
        Load license from file with refresh detection.
        
        Args:
            force_refresh: Force reload even if file hasn't changed
        
        Returns:
            License object or None if not found/invalid
        """
        license_path = self.get_license_path()
        
        if not license_path.exists():
            logger.warning(f"License file not found at {license_path}")
            return None
        
        # Check if license file has been updated
        try:
            current_mtime = license_path.stat().st_mtime
            if not force_refresh and self._last_license_mtime == current_mtime:
                # File hasn't changed, return cached license
                return self._cached_license
            self._last_license_mtime = current_mtime
        except Exception:
            pass  # Continue with loading
        
        license = License.load_from_file(license_path)
        if not license:
            logger.warning(f"Failed to load license from {license_path}")
            return None
        
        logger.info(f"License loaded from {license_path}")
        return license
    
    def is_offline(self) -> bool:
        """
        Check if system is offline (cannot reach internet).
        
        Returns:
            True if offline, False if online
        """
        try:
            # Try to connect to a reliable host (Google DNS)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return False
        except (socket.error, OSError):
            return True
    
    def validate_license(self, license: Optional[License] = None) -> LicenseStatus:
        """
        Validate a license.
        
        Args:
            license: License to validate (if None, loads from file)
            
        Returns:
            LicenseStatus indicating validation result
        """
        if license is None:
            license = self.load_license()
        
        if license is None:
            return LicenseStatus.NOT_FOUND
        
        # Check version compatibility
        if license.version != self.app_version:
            logger.warning(f"License version {license.version} does not match app version {self.app_version}")
            return LicenseStatus.VERSION_MISMATCH
        
        # Get embedded public key
        public_key = get_embedded_public_key()
        if not public_key:
            logger.error("Public key not found - cannot verify license")
            return LicenseStatus.INVALID_SIGNATURE
        
        # Verify signature
        if not verify_license_signature(license, public_key):
            return LicenseStatus.INVALID_SIGNATURE
        
        # Check expiration with clock skew tolerance
        if license.is_expired(clock_skew_tolerance_minutes=self.clock_skew_tolerance_minutes):
            logger.warning(f"License expired on {license.expires}")
            return LicenseStatus.EXPIRED
        
        # License is valid
        logger.info(f"License validated successfully for {license.company}")
        return LicenseStatus.VALID
    
    def get_license_status(self, force_reload: bool = False) -> LicenseStatus:
        """
        Get current license status (with caching).
        
        Args:
            force_reload: Force reload of license from file
            
        Returns:
            LicenseStatus
        """
        if force_reload or self._cached_status is None:
            license = self.load_license()
            self._cached_license = license
            self._cached_status = self.validate_license(license)
        
        return self._cached_status
    
    def is_license_valid(self) -> bool:
        """
        Check if license is currently valid.
        
        Returns:
            True if license is valid, False otherwise
        """
        status = self.get_license_status()
        return status == LicenseStatus.VALID
    
    def get_license_error_message(self, status: Optional[LicenseStatus] = None) -> str:
        """
        Get user-friendly error message for license status with actionable guidance.
        
        Args:
            status: License status (if None, uses current status)
            
        Returns:
            Error message string with actionable guidance
        """
        if status is None:
            status = self.get_license_status()
        
        # Check for offline mode
        if self.is_offline() and status != LicenseStatus.VALID:
            offline_note = " (System appears to be offline - license check may be affected)"
        else:
            offline_note = ""
        
        messages = {
            LicenseStatus.VALID: "License is valid.",
            LicenseStatus.EXPIRED: (
                "License has expired. Please contact support to renew your license. "
                "You can update the license file and restart the application."
            ),
            LicenseStatus.INVALID_SIGNATURE: (
                "License signature is invalid. This may indicate a corrupted license file. "
                "Please contact support to obtain a new license file."
            ),
            LicenseStatus.NOT_FOUND: (
                "License file not found. Please ensure license.json is in the application directory "
                f"or in {Path.home() / '.pdf_merger'}. Contact support if you need a license file."
            ),
            LicenseStatus.INVALID_FORMAT: (
                "License file format is invalid. Please ensure the license.json file is valid JSON. "
                "Contact support if you need a new license file."
            ),
            LicenseStatus.VERSION_MISMATCH: (
                f"License version does not match application version ({self.app_version}). "
                "Please contact support to obtain a license for this version."
            ),
        }
        
        base_message = messages.get(status, "Unknown license error. Please contact support.")
        return base_message + offline_note
    
    def get_expiry_warning_message(self) -> Optional[str]:
        """
        Get expiry warning message if license is expiring soon.
        
        Returns:
            Warning message string or None if no warning needed
        """
        license = self._cached_license or self.load_license()
        if not license:
            return None
        
        warning_level = license.get_expiry_warning_level()
        if warning_level is None:
            return None
        
        days = license.days_until_expiry()
        
        if warning_level == WarningLevel.EXPIRED:
            return f"License expired on {license.expires}. Please renew immediately."
        elif warning_level == WarningLevel.CRITICAL:
            return f"License expires in {days} days ({license.expires}). Please renew soon."
        elif warning_level == WarningLevel.WARNING:
            return f"License expires in {days} days ({license.expires}). Consider renewing."
        elif warning_level == WarningLevel.INFO:
            return f"License expires in {days} days ({license.expires})."
        
        return None
    
    def get_license_info(self) -> Optional[dict]:
        """
        Get license information (if valid).
        
        Returns:
            Dictionary with license info or None if invalid
        """
        if not self.is_license_valid():
            return None
        
        if self._cached_license is None:
            self._cached_license = self.load_license()
        
        if self._cached_license is None:
            return None
        
        days_until_expiry = self._cached_license.days_until_expiry()
        warning_level = self._cached_license.get_expiry_warning_level()
        
        return {
            'company': self._cached_license.company,
            'expires': self._cached_license.expires,
            'days_until_expiry': days_until_expiry,
            'expiry_warning_level': warning_level.value if warning_level else None,
            'allowed_machines': self._cached_license.allowed_machines,
            'version': self._cached_license.version,
        }
