"""
Unit tests for ProcessingResult (merge_processor result type).
"""

from pdf_merger.core.result_types import ProcessingResult


class TestProcessingResult:
    """Test cases for ProcessingResult dataclass."""

    def test_processing_result_creation(self):
        """Test creating a ProcessingResult instance."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=8,
            failed_rows=[3, 7]
        )
        assert result.total_rows == 10
        assert result.successful_merges == 8
        assert result.failed_rows == [3, 7]

    def test_processing_result_string_representation(self):
        """Test string representation of ProcessingResult."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=8,
            failed_rows=[3, 7]
        )
        str_repr = str(result)
        assert "Total rows processed: 10" in str_repr
        assert "Successfully merged PDFs: 8" in str_repr
        assert "Failed rows: 2" in str_repr
