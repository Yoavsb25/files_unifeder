"""
License model.
Data structures for license information.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..enums import WarningLevel
from ..constants import Constants


@dataclass
class License:
    """License information."""
    company: str
    expires: str  # ISO format date string: YYYY-MM-DD
    allowed_machines: int
    version: str
    signature: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert license to dictionary (without signature for signing)."""
        data = asdict(self)
        # Remove signature before signing
        data.pop('signature', None)
        return data
    
    def to_dict_with_signature(self) -> dict:
        """Convert license to dictionary (with signature)."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'License':
        """Create license from dictionary."""
        return cls(
            company=data.get('company', ''),
            expires=data.get('expires', ''),
            allowed_machines=data.get('allowed_machines', 0),
            version=data.get('version', '1.0.0'),
            signature=data.get('signature')
        )
    
    def is_expired(self, clock_skew_tolerance_minutes: int = Constants.LICENSE_CLOCK_SKEW_TOLERANCE_MINUTES) -> bool:
        """
        Check if license is expired with clock skew tolerance.
        
        Args:
            clock_skew_tolerance_minutes: Tolerance for clock skew in minutes (default: 5 minutes)
        
        Returns:
            True if expired, False otherwise
        """
        try:
            expiry_date = datetime.strptime(self.expires, Constants.LICENSE_DATE_FORMAT).date()
            today = datetime.now().date()
            
            # If expiry date is today or in the future, license is not expired
            if expiry_date >= today:
                return False
            
            # If expiry date is in the past, apply clock skew tolerance
            # This handles minor clock differences between systems
            # Tolerance allows licenses to remain valid for a few minutes past midnight
            from datetime import timedelta
            tolerance = timedelta(minutes=clock_skew_tolerance_minutes)
            effective_expiry = datetime.combine(expiry_date, datetime.min.time()) + tolerance
            
            return datetime.now() > effective_expiry
        except (ValueError, TypeError):
            return True
    
    def days_until_expiry(self) -> Optional[int]:
        """
        Get number of days until license expires.
        
        Returns:
            Number of days until expiry, or None if invalid
        """
        try:
            expiry_date = datetime.strptime(self.expires, Constants.LICENSE_DATE_FORMAT).date()
            today = datetime.now().date()
            delta = expiry_date - today
            return delta.days
        except (ValueError, TypeError):
            return None
    
    def get_expiry_warning_level(self) -> Optional[WarningLevel]:
        """
        Get expiry warning level based on days until expiry.
        
        Returns:
            WarningLevel enum value or None if no warning needed
        """
        days = self.days_until_expiry()
        if days is None:
            return None
        
        if days < 0:
            return WarningLevel.EXPIRED
        elif days <= Constants.LICENSE_WARNING_CRITICAL_DAYS:
            return WarningLevel.CRITICAL
        elif days <= Constants.LICENSE_WARNING_WARNING_DAYS:
            return WarningLevel.WARNING
        elif days <= Constants.LICENSE_WARNING_INFO_DAYS:
            return WarningLevel.INFO
        
        return None
    
    def to_json_string(self) -> str:
        """Convert license to JSON string (without signature for signing)."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['License']:
        """Load license from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return None
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save license to JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict_with_signature(), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
