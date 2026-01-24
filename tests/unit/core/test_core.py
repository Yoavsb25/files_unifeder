"""
Unit tests for core module (merger and reporter).
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.core.merger import run_merge
from pdf_merger.core.reporter import format_result_summary, format_result_detailed
from pdf_merger.processor import ProcessingResult


class TestRunMerge:
    """Test cases for run_merge function."""
    
    @patch('pdf_merger.core.merger.process_file')
    @patch('pdf_merger.core.merger.logger')
    def test_run_merge_success(self, mock_logger, mock_process_file, tmp_path):
        """Test successful merge operation."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        expected_result = ProcessingResult(
            total_rows=5,
            successful_merges=4,
            failed_rows=[3]
        )
        mock_process_file.return_value = expected_result
        
        result = run_merge(input_file, pdf_dir, output_dir)
        
        assert result == expected_result
        mock_process_file.assert_called_once_with(
            file_path=input_file,
            source_folder=pdf_dir,
            output_folder=output_dir,
            required_column='serial_numbers'
        )
        assert mock_logger.info.called
    
    @patch('pdf_merger.core.merger.process_file')
    @patch('pdf_merger.core.merger.logger')
    def test_run_merge_with_custom_column(self, mock_logger, mock_process_file, tmp_path):
        """Test merge operation with custom required column."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        expected_result = ProcessingResult(
            total_rows=2,
            successful_merges=2,
            failed_rows=[]
        )
        mock_process_file.return_value = expected_result
        
        result = run_merge(input_file, pdf_dir, output_dir, required_column="custom_column")
        
        assert result == expected_result
        mock_process_file.assert_called_once_with(
            file_path=input_file,
            source_folder=pdf_dir,
            output_folder=output_dir,
            required_column="custom_column"
        )
    
    @patch('pdf_merger.core.merger.process_file')
    @patch('pdf_merger.core.merger.logger')
    def test_run_merge_exception(self, mock_logger, mock_process_file, tmp_path):
        """Test merge operation when exception occurs."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_process_file.side_effect = ValueError("Processing error")
        
        with pytest.raises(ValueError, match="Processing error"):
            run_merge(input_file, pdf_dir, output_dir)
        
        assert mock_logger.error.called
        error_call = str(mock_logger.error.call_args)
        assert "Error during merge operation" in error_call


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
        assert "Failed or skipped rows: 0" in report
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
        assert "Failed or skipped rows: 3" in report
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
        assert "Failed or skipped rows: 0" in report
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
