"""
License model.
Data structures for license information.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


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
    
    def is_expired(self) -> bool:
        """Check if license is expired."""
        try:
            expiry_date = datetime.strptime(self.expires, '%Y-%m-%d').date()
            today = datetime.now().date()
            return today > expiry_date
        except (ValueError, TypeError):
            return True
    
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
