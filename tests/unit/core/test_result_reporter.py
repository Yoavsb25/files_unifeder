"""
Unit tests for result_reporter module.
"""

import pytest
from pathlib import Path
from pdf_merger.core.result_reporter import format_result_summary, format_result_detailed
from pdf_merger.core.result_types import ProcessingResult
from pdf_merger.models import MergeResult, RowResult, RowStatus


class TestFormatResultSummary:
    """Test cases for format_result_summary function."""
    
    def test_format_result_summary_success(self):
        """Test formatting summary with successful results."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=10,
            failed_rows=[]
        )
        
        summary = format_result_summary(result)
        
        assert "Processing Complete" in summary
        assert "Total rows processed: 10" in summary
        assert "Successfully merged PDFs: 10" in summary
        assert "Failed rows: 0" in summary
        assert "=" * 60 in summary
    
    def test_format_result_summary_with_failures(self):
        """Test formatting summary with failed rows."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=7,
            failed_rows=[2, 5, 8]
        )
        
        summary = format_result_summary(result)
        
        assert "Total rows processed: 10" in summary
        assert "Successfully merged PDFs: 7" in summary
        assert "Failed rows: 3" in summary
        assert "Failed row numbers: 2, 5, 8" in summary
    
    def test_format_result_summary_long_failed_list(self):
        """Test formatting summary with many failed rows (truncation)."""
        result = ProcessingResult(
            total_rows=100,
            successful_merges=50,
            failed_rows=list(range(1, 51))  # 50 failed rows
        )
        
        summary = format_result_summary(result)
        
        assert "Failed rows: 50" in summary
        # Should truncate long list
        if "Failed row numbers:" in summary:
            failed_line = [line for line in summary.split('\n') if 'Failed row numbers:' in line][0]
            assert len(failed_line) <= 100 or "..." in failed_line
    
    def test_format_result_summary_empty(self):
        """Test formatting summary with empty result."""
        result = ProcessingResult(
            total_rows=0,
            successful_merges=0,
            failed_rows=[]
        )
        
        summary = format_result_summary(result)
        
        assert "Total rows processed: 0" in summary
        assert "Successfully merged PDFs: 0" in summary
        assert "Failed rows: 0" in summary
    
    def test_format_result_summary_with_mergeresult_skipped(self):
        """Test formatting summary with MergeResult containing skipped rows."""
        result = MergeResult(
            total_rows=10,
            successful_merges=7,
            failed_rows=[2],
            skipped_rows=[1, 3]
        )
        
        summary = format_result_summary(result)
        
        assert "Total rows processed: 10" in summary
        assert "Successfully merged PDFs: 7" in summary
        assert "Failed rows: 1" in summary
        assert "Skipped rows: 2" in summary


class TestFormatResultDetailed:
    """Test cases for format_result_detailed function."""
    
    def test_format_result_detailed_success(self):
        """Test formatting detailed report with successful results."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=10,
            failed_rows=[]
        )
        
        report = format_result_detailed(result)
        
        assert "Detailed Processing Report" in report
        assert "Total rows in input file: 10" in report
        assert "Successfully merged PDFs: 10" in report
        assert "Failed rows: 0" in report
        assert "Success rate: 100.0%" in report
        assert "=" * 60 in report
    
    def test_format_result_detailed_with_failures(self):
        """Test formatting detailed report with failed rows."""
        result = ProcessingResult(
            total_rows=10,
            successful_merges=7,
            failed_rows=[2, 5, 8]
        )
        
        report = format_result_detailed(result)
        
        assert "Total rows in input file: 10" in report
        assert "Successfully merged PDFs: 7" in report
        assert "Failed rows: 3" in report
        assert "Success rate: 70.0%" in report
        assert "Failed/Skipped Row Numbers:" in report
        assert "  - Row 2" in report
        assert "  - Row 5" in report
        assert "  - Row 8" in report
    
    def test_format_result_detailed_empty(self):
        """Test formatting detailed report with empty result."""
        result = ProcessingResult(
            total_rows=0,
            successful_merges=0,
            failed_rows=[]
        )
        
        report = format_result_detailed(result)
        
        assert "Total rows in input file: 0" in report
        assert "Successfully merged PDFs: 0" in report
        assert "Failed rows: 0" in report
        assert "Success rate: 0.0%" in report
    
    def test_format_result_detailed_partial_success(self):
        """Test formatting detailed report with partial success."""
        result = ProcessingResult(
            total_rows=5,
            successful_merges=3,
            failed_rows=[1, 4]
        )
        
        report = format_result_detailed(result)
        
        assert "Success rate: 60.0%" in report
        assert "  - Row 1" in report
        assert "  - Row 4" in report
    
    def test_format_result_detailed_with_mergeresult(self):
        """Test formatting detailed report with MergeResult."""
        # Start with 0 successful_merges - add_row_result will update counters
        result = MergeResult(
            total_rows=10,
            successful_merges=0,
            failed_rows=[],
            skipped_rows=[]
        )
        
        # Add some row results - these will update the counters
        result.add_row_result(RowResult(0, RowStatus.SUCCESS))
        result.add_row_result(RowResult(1, RowStatus.SKIPPED, error_message="No serial numbers"))
        result.add_row_result(RowResult(2, RowStatus.FAILED, error_message="File not found", files_missing=["GRNW_123"]))
        
        report = format_result_detailed(result)
        
        assert "Total rows in input file: 10" in report
        assert "Successfully merged PDFs: 1" in report  # Only 1 success from add_row_result
        assert "Failed rows: 1" in report  # Only 1 failed from add_row_result
        assert "Skipped rows: 1" in report  # Only 1 skipped from add_row_result
        assert "Success rate: 10.0%" in report  # 1 out of 10
        assert "Failed Row Numbers:" in report
        assert "Skipped Row Numbers:" in report
        assert "Row Details:" in report
        assert "FAILED" in report
        assert "SKIPPED" in report
    
    def test_format_result_detailed_with_mergeresult_partial(self):
        """Test formatting detailed report with MergeResult containing partial results."""
        result = MergeResult(
            total_rows=5,
            successful_merges=3
        )
        
        # Add partial result
        partial_result = RowResult(
            0,
            RowStatus.PARTIAL,
            files_found=[Path("/tmp/file1.pdf")],
            files_missing=["GRNW_123"]
        )
        result.add_row_result(partial_result)
        
        report = format_result_detailed(result)
        
        assert "PARTIAL" in report
        assert "Some files missing" in report
        assert "Missing files: GRNW_123" in report
    
    def test_format_result_detailed_with_processing_time(self):
        """Test formatting detailed report with processing time."""
        result = MergeResult(
            total_rows=10,
            successful_merges=10,
            total_processing_time=5.5
        )
        
        report = format_result_detailed(result)
        
        assert "Total processing time: 5.50 seconds" in report
