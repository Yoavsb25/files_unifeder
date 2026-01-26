"""
Unit tests for merge_result module.
"""

import pytest
from pathlib import Path
from pdf_merger.models.merge_result import (
    RowResult,
    RowStatus,
    MergeResult
)
from pdf_merger.core.merge_processor import ProcessingResult


class TestRowResult:
    """Test cases for RowResult class."""
    
    def test_row_result_success(self):
        """Test RowResult with SUCCESS status."""
        output_file = Path("/tmp/test.pdf")
        result = RowResult(
            row_index=0,
            status=RowStatus.SUCCESS,
            output_file=output_file
        )
        
        assert result.row_index == 0
        assert result.status == RowStatus.SUCCESS
        assert result.output_file == output_file
        assert result.is_success() is True
        assert result.is_failed() is False
        assert result.is_skipped() is False
    
    def test_row_result_failed(self):
        """Test RowResult with FAILED status."""
        result = RowResult(
            row_index=1,
            status=RowStatus.FAILED,
            error_message="File not found"
        )
        
        assert result.row_index == 1
        assert result.status == RowStatus.FAILED
        assert result.error_message == "File not found"
        assert result.is_success() is False
        assert result.is_failed() is True
        assert result.is_skipped() is False
    
    def test_row_result_skipped(self):
        """Test RowResult with SKIPPED status."""
        result = RowResult(
            row_index=2,
            status=RowStatus.SKIPPED,
            error_message="No serial numbers"
        )
        
        assert result.row_index == 2
        assert result.status == RowStatus.SKIPPED
        assert result.is_success() is False
        assert result.is_failed() is False
        assert result.is_skipped() is True
    
    def test_row_result_partial(self):
        """Test RowResult with PARTIAL status."""
        result = RowResult(
            row_index=3,
            status=RowStatus.PARTIAL,
            files_found=[Path("/tmp/file1.pdf")],
            files_missing=["GRNW_123"]
        )
        
        assert result.row_index == 3
        assert result.status == RowStatus.PARTIAL
        assert len(result.files_found) == 1
        assert len(result.files_missing) == 1
        assert result.is_success() is False
        assert result.is_failed() is False
        assert result.is_skipped() is False
    
    def test_row_result_with_processing_time(self):
        """Test RowResult with processing time."""
        result = RowResult(
            row_index=0,
            status=RowStatus.SUCCESS,
            processing_time=1.5
        )
        
        assert result.processing_time == 1.5
    
    def test_row_result_str_with_output_file(self):
        """Test RowResult string representation with output file."""
        output_file = Path("/tmp/test.pdf")
        result = RowResult(
            row_index=0,
            status=RowStatus.SUCCESS,
            output_file=output_file
        )
        
        str_repr = str(result)
        assert "Row 1" in str_repr
        assert "SUCCESS" in str_repr
        assert "test.pdf" in str_repr
    
    def test_row_result_str_without_output_file(self):
        """Test RowResult string representation without output file."""
        result = RowResult(
            row_index=1,
            status=RowStatus.FAILED
        )
        
        str_repr = str(result)
        assert "Row 2" in str_repr
        assert "FAILED" in str_repr


class TestMergeResult:
    """Test cases for MergeResult class."""
    
    def test_merge_result_basic(self):
        """Test basic MergeResult creation."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8
        )
        
        assert result.total_rows == 10
        assert result.successful_merges == 8
        assert len(result.failed_rows) == 0
        assert len(result.skipped_rows) == 0
        assert len(result.row_results) == 0
    
    def test_merge_result_with_failed_rows(self):
        """Test MergeResult with failed rows."""
        result = MergeResult(
            total_rows=10,
            successful_merges=7,
            failed_rows=[2, 5]
        )
        
        assert result.total_rows == 10
        assert result.successful_merges == 7
        assert result.failed_rows == [2, 5]
    
    def test_merge_result_with_skipped_rows(self):
        """Test MergeResult with skipped rows."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8,
            skipped_rows=[1, 3]
        )
        
        assert result.total_rows == 10
        assert result.successful_merges == 8
        assert result.skipped_rows == [1, 3]
    
    def test_merge_result_with_job_id(self):
        """Test MergeResult with job_id."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8,
            job_id="job-123"
        )
        
        assert result.job_id == "job-123"
    
    def test_merge_result_from_processing_result(self):
        """Test creating MergeResult from ProcessingResult."""
        processing_result = ProcessingResult(
            total_rows=10,
            successful_merges=8,
            failed_rows=[2, 5]
        )
        
        merge_result = MergeResult.from_processing_result(
            processing_result,
            job_id="job-123"
        )
        
        assert merge_result.total_rows == 10
        assert merge_result.successful_merges == 8
        assert merge_result.failed_rows == [2, 5]
        assert merge_result.skipped_rows == []
        assert merge_result.job_id == "job-123"
        assert len(merge_result.row_results) == 0
    
    def test_add_row_result_success(self):
        """Test adding a successful row result."""
        result = MergeResult(total_rows=1, successful_merges=0)
        row_result = RowResult(
            row_index=0,
            status=RowStatus.SUCCESS,
            output_file=Path("/tmp/test.pdf")
        )
        
        result.add_row_result(row_result)
        
        assert result.successful_merges == 1
        assert len(result.failed_rows) == 0
        assert len(result.skipped_rows) == 0
        assert len(result.row_results) == 1
        assert result.row_results[0] == row_result
    
    def test_add_row_result_failed(self):
        """Test adding a failed row result."""
        result = MergeResult(total_rows=1, successful_merges=0)
        row_result = RowResult(
            row_index=0,
            status=RowStatus.FAILED,
            error_message="Error"
        )
        
        result.add_row_result(row_result)
        
        assert result.successful_merges == 0
        assert result.failed_rows == [0]
        assert len(result.skipped_rows) == 0
        assert len(result.row_results) == 1
    
    def test_add_row_result_skipped(self):
        """Test adding a skipped row result."""
        result = MergeResult(total_rows=1, successful_merges=0)
        row_result = RowResult(
            row_index=0,
            status=RowStatus.SKIPPED
        )
        
        result.add_row_result(row_result)
        
        assert result.successful_merges == 0
        assert len(result.failed_rows) == 0
        assert result.skipped_rows == [0]
        assert len(result.row_results) == 1
    
    def test_get_success_rate(self):
        """Test calculating success rate."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8
        )
        
        assert result.get_success_rate() == 80.0
    
    def test_get_success_rate_zero_rows(self):
        """Test success rate with zero rows."""
        result = MergeResult(
            total_rows=0,
            successful_merges=0
        )
        
        assert result.get_success_rate() == 0.0
    
    def test_get_success_rate_partial(self):
        """Test success rate with partial success."""
        result = MergeResult(
            total_rows=3,
            successful_merges=1
        )
        
        rate = result.get_success_rate()
        assert abs(rate - 33.333) < 0.1
    
    def test_get_failed_row_results(self):
        """Test getting failed row results."""
        result = MergeResult(total_rows=3, successful_merges=0)
        
        success_result = RowResult(0, RowStatus.SUCCESS)
        failed_result1 = RowResult(1, RowStatus.FAILED)
        failed_result2 = RowResult(2, RowStatus.FAILED)
        
        result.add_row_result(success_result)
        result.add_row_result(failed_result1)
        result.add_row_result(failed_result2)
        
        failed_results = result.get_failed_row_results()
        
        assert len(failed_results) == 2
        assert failed_result1 in failed_results
        assert failed_result2 in failed_results
        assert success_result not in failed_results
    
    def test_get_skipped_row_results(self):
        """Test getting skipped row results."""
        result = MergeResult(total_rows=3, successful_merges=0)
        
        success_result = RowResult(0, RowStatus.SUCCESS)
        skipped_result1 = RowResult(1, RowStatus.SKIPPED)
        skipped_result2 = RowResult(2, RowStatus.SKIPPED)
        
        result.add_row_result(success_result)
        result.add_row_result(skipped_result1)
        result.add_row_result(skipped_result2)
        
        skipped_results = result.get_skipped_row_results()
        
        assert len(skipped_results) == 2
        assert skipped_result1 in skipped_results
        assert skipped_result2 in skipped_results
        assert success_result not in skipped_results
    
    def test_merge_result_str(self):
        """Test MergeResult string representation."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8,
            failed_rows=[2, 5],
            skipped_rows=[1]
        )
        
        str_repr = str(result)
        assert "total_rows=10" in str_repr
        assert "successful=8" in str_repr
        assert "failed=2" in str_repr
        assert "skipped=1" in str_repr
    
    def test_merge_result_with_processing_time(self):
        """Test MergeResult with total processing time."""
        result = MergeResult(
            total_rows=10,
            successful_merges=8,
            total_processing_time=5.5
        )
        
        assert result.total_processing_time == 5.5
