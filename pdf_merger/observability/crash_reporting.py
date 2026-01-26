"""
Crash reporting module.
Opt-in crash reporting with stack traces.
"""

import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..utils.logging_utils import get_logger

logger = get_logger("observability.crash_reporting")


class CrashReporter:
    """
    Crash reporter for collecting and reporting application crashes.
    
    All crash reporting is opt-in. Reports are stored locally and can be
    optionally sent to a crash reporting service.
    """
    
    def __init__(self, enabled: bool = False, report_dir: Optional[Path] = None):
        """
        Initialize crash reporter.
        
        Args:
            enabled: Whether crash reporting is enabled (default: False, opt-in)
            report_dir: Directory to store crash reports (default: ~/.pdf_merger/crashes)
        """
        self.enabled = enabled
        
        if report_dir is None:
            report_dir = Path.home() / '.pdf_merger' / 'crashes'
        
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def report_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        Report an exception with stack trace.
        
        Args:
            exception: The exception that occurred
            context: Optional context information
            
        Returns:
            Path to crash report file if saved, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            # Generate crash report
            report = self._generate_report(exception, context)
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.report_dir / f"crash_{timestamp}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Crash report saved to {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to save crash report: {e}")
            return None
    
    def _generate_report(self, exception: Exception, context: Optional[Dict[str, Any]]) -> str:
        """
        Generate crash report text.
        
        Args:
            exception: The exception
            context: Optional context
            
        Returns:
            Crash report as string
        """
        lines = [
            "=" * 80,
            "PDF Batch Merger - Crash Report",
            "=" * 80,
            "",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Exception Type: {type(exception).__name__}",
            f"Exception Message: {str(exception)}",
            "",
            "Stack Trace:",
            "-" * 80,
        ]
        
        # Add stack trace
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            lines.extend(traceback.format_exception(exc_type, exc_value, exc_traceback))
        else:
            lines.append(str(exception))
        
        lines.append("")
        lines.append("-" * 80)
        
        # Add context if provided
        if context:
            lines.append("")
            lines.append("Context:")
            lines.append("-" * 80)
            for key, value in context.items():
                lines.append(f"{key}: {value}")
            lines.append("")
        
        # Add system information
        import platform
        lines.append("System Information:")
        lines.append("-" * 80)
        lines.append(f"Platform: {platform.system()} {platform.release()}")
        lines.append(f"Python Version: {platform.python_version()}")
        lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def install_exception_hook(self) -> None:
        """
        Install global exception hook to catch unhandled exceptions.
        """
        if not self.enabled:
            return
        
        def exception_hook(exc_type, exc_value, exc_traceback):
            # Call original hook first
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            
            # Report the exception
            if issubclass(exc_type, Exception):
                self.report_exception(exc_value)
        
        sys.excepthook = exception_hook
        logger.debug("Crash reporting exception hook installed")


# Global crash reporter instance
_crash_reporter: Optional[CrashReporter] = None


def get_crash_reporter(enabled: bool = False) -> CrashReporter:
    """
    Get or create the global crash reporter.
    
    Args:
        enabled: Whether crash reporting is enabled (default: False, opt-in)
        
    Returns:
        CrashReporter instance
    """
    global _crash_reporter
    if _crash_reporter is None:
        _crash_reporter = CrashReporter(enabled=enabled)
    return _crash_reporter
