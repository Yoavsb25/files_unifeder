"""
License manager.
Main license validation and verification logic.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from .license_model import License
from .license_signer import get_embedded_public_key, verify_license_signature
from ..logger import get_logger

logger = get_logger("licensing.manager")


class LicenseStatus(Enum):
    """License validation status."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID_SIGNATURE = "invalid_signature"
    NOT_FOUND = "not_found"
    INVALID_FORMAT = "invalid_format"
    VERSION_MISMATCH = "version_mismatch"


class LicenseManager:
    """Manages license validation and verification."""
    
    def __init__(self, app_version: str = "1.0.0"):
        """
        Initialize license manager.
        
        Args:
            app_version: Current application version
        """
        self.app_version = app_version
        self._cached_license: Optional[License] = None
        self._cached_status: Optional[LicenseStatus] = None
    
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
    
    def load_license(self) -> Optional[License]:
        """
        Load license from file.
        
        Returns:
            License object or None if not found/invalid
        """
        license_path = self.get_license_path()
        
        if not license_path.exists():
            logger.warning(f"License file not found at {license_path}")
            return None
        
        license = License.load_from_file(license_path)
        if not license:
            logger.warning(f"Failed to load license from {license_path}")
            return None
        
        logger.info(f"License loaded from {license_path}")
        return license
    
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
        
        # Check expiration
        if license.is_expired():
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
        Get user-friendly error message for license status.
        
        Args:
            status: License status (if None, uses current status)
            
        Returns:
            Error message string
        """
        if status is None:
            status = self.get_license_status()
        
        messages = {
            LicenseStatus.VALID: "License is valid.",
            LicenseStatus.EXPIRED: "License has expired. Please contact support to renew.",
            LicenseStatus.INVALID_SIGNATURE: "License signature is invalid. Please contact support.",
            LicenseStatus.NOT_FOUND: "License file not found. Please ensure license.json is in the application directory.",
            LicenseStatus.INVALID_FORMAT: "License file format is invalid. Please contact support.",
            LicenseStatus.VERSION_MISMATCH: f"License version does not match application version ({self.app_version}). Please contact support.",
        }
        
        return messages.get(status, "Unknown license error. Please contact support.")
    
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
        
        return {
            'company': self._cached_license.company,
            'expires': self._cached_license.expires,
            'allowed_machines': self._cached_license.allowed_machines,
            'version': self._cached_license.version,
        }
