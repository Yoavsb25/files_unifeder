"""
Metrics collection module.
Collects and tracks application metrics.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

from ..logger import get_logger

logger = get_logger("observability.metrics")


@dataclass
class Metric:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores application metrics.
    
    Metrics collected:
    - Processing time per row
    - File sizes processed
    - Memory usage (if available)
    - Success/failure rates
    - Match ambiguity counts
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize metrics collector.
        
        Args:
            enabled: Whether metrics collection is enabled
        """
        self.enabled = enabled
        self.metrics: List[Metric] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a counter metric.
        
        Args:
            name: Metric name
            value: Counter increment (default: 1)
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return
        
        self.counters[name] += value
        self.metrics.append(Metric(
            name=name,
            value=float(value),
            timestamp=time.time(),
            tags=tags or {}
        ))
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timer metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return
        
        self.timers[name].append(duration)
        self.metrics.append(Metric(
            name=name,
            value=duration,
            timestamp=time.time(),
            tags=tags or {}
        ))
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a gauge metric (current value at a point in time).
        
        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return
        
        self.metrics.append(Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        ))
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, 0)
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """
        Get timer statistics.
        
        Returns:
            Dictionary with min, max, avg, count
        """
        values = self.timers.get(name, [])
        if not values:
            return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
        
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
    
    def get_summary(self) -> Dict:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with metric summaries
        """
        return {
            'counters': dict(self.counters),
            'timers': {name: self.get_timer_stats(name) for name in self.timers},
            'total_metrics': len(self.metrics)
        }
    
    def clear(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(enabled: bool = True) -> MetricsCollector:
    """
    Get or create the global metrics collector.
    
    Args:
        enabled: Whether metrics collection is enabled
        
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(enabled=enabled)
    return _metrics_collector
