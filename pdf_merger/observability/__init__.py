"""
Observability package.
Provides metrics, telemetry, and crash reporting (opt-in).
"""

from .metrics import MetricsCollector, get_metrics_collector
from .telemetry import TelemetryService, get_telemetry_service
from .crash_reporting import CrashReporter, get_crash_reporter

__all__ = [
    'MetricsCollector',
    'get_metrics_collector',
    'TelemetryService',
    'get_telemetry_service',
    'CrashReporter',
    'get_crash_reporter',
]
