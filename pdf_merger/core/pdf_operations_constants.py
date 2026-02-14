"""PDF operations and streaming constants for PDF Merger."""


class PdfOperationsConstants:
    """Streaming thresholds and PDF operation settings."""
    STREAMING_THRESHOLD_MB = 100.0
    STREAMING_CHUNK_SIZE = 10
    STREAMING_PROGRESS_INTERVAL = 50
    BYTES_PER_MB = 1024 * 1024
    MEMORY_MULTIPLIER_ESTIMATE = 2.5
