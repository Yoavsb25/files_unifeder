"""
Telemetry module.
Opt-in anonymous usage statistics collection.
"""

import json
import platform
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path

from ..utils.logging_utils import get_logger
from .. import APP_VERSION

logger = get_logger("observability.telemetry")


@dataclass
class TelemetryEvent:
    """A telemetry event."""
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    session_id: Optional[str] = None


class TelemetryService:
    """
    Telemetry service for collecting anonymous usage statistics.
    
    All telemetry is opt-in and anonymized. No personal data is collected.
    """
    
    def __init__(self, enabled: bool = False, endpoint: Optional[str] = None):
        """
        Initialize telemetry service.
        
        Args:
            enabled: Whether telemetry is enabled (default: False, opt-in)
            endpoint: Optional telemetry endpoint URL (for future use)
        """
        self.enabled = enabled
        self.endpoint = endpoint
        self.events: list[TelemetryEvent] = []
        self.session_id: Optional[str] = None
    
    def record_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a telemetry event.
        
        Args:
            event_type: Type of event (e.g., 'merge_completed', 'error_occurred')
            data: Optional event data (anonymized)
        """
        if not self.enabled:
            return
        
        import time
        event = TelemetryEvent(
            event_type=event_type,
            timestamp=time.time(),
            data=data or {},
            session_id=self.session_id
        )
        
        self.events.append(event)
        logger.debug(f"Telemetry event recorded: {event_type}")
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get anonymized system information.
        
        Returns:
            Dictionary with system info (no personal data)
        """
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'app_version': APP_VERSION,
            # No machine identifiers, usernames, or personal data
        }
    
    def flush(self) -> None:
        """
        Flush telemetry events (for future implementation with endpoint).
        Currently just logs that telemetry would be sent.
        """
        if not self.enabled or not self.events:
            return
        
        if self.endpoint:
            # Future: Send to endpoint
            logger.debug(f"Would send {len(self.events)} telemetry events to {self.endpoint}")
        else:
            # For now, just log that telemetry was collected
            logger.debug(f"Telemetry collected: {len(self.events)} events (not sent, endpoint not configured)")
        
        self.events.clear()


# Global telemetry service instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service(enabled: bool = False) -> TelemetryService:
    """
    Get or create the global telemetry service.
    
    Args:
        enabled: Whether telemetry is enabled (default: False, opt-in)
        
    Returns:
        TelemetryService instance
    """
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService(enabled=enabled)
    return _telemetry_service
