"""
Observability package.
Provides metrics, telemetry, and crash reporting (opt-in).
Metrics are process-global and initialized once in main; the processor only
records (record_counter, record_timer, record_gauge), never creates the collector.
"""

from .metrics import MetricsCollector, MetricsRecorder, get_metrics_collector
from .telemetry import TelemetryService, get_telemetry_service
from .crash_reporting import CrashReporter, get_crash_reporter

__all__ = [
    'MetricsCollector',
    'MetricsRecorder',
    'get_metrics_collector',
    'TelemetryService',
    'get_telemetry_service',
    'CrashReporter',
    'get_crash_reporter',
]
