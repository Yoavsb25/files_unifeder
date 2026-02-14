"""
Unit tests for merge_orchestrator module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.core.constants import Constants
from pdf_merger.core.merge_orchestrator import run_merge, run_merge_job
from pdf_merger.models import MergeResult


class TestRunMerge:
    """Test cases for run_merge function. Legacy entry point; delegates to run_merge_job and returns MergeResult."""
    
    @patch('pdf_merger.core.merge_orchestrator.run_merge_job')
    def test_run_merge_success(self, mock_run_merge_job, tmp_path):
        """Test successful merge operation (run_merge delegates to run_merge_job)."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        expected_result = MergeResult(
            total_rows=5,
            successful_merges=4,
            failed_rows=[3]
        )
        mock_run_merge_job.return_value = expected_result
        
        result = run_merge(input_file, pdf_dir, output_dir)
        
        assert result == expected_result
        mock_run_merge_job.assert_called_once()
        call_kwargs = mock_run_merge_job.call_args[1]
        assert call_kwargs["input_file"] == input_file
        assert call_kwargs["pdf_dir"] == pdf_dir
        assert call_kwargs["output_dir"] == output_dir
        assert call_kwargs["required_column"] == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
    
    @patch('pdf_merger.core.merge_orchestrator.run_merge_job')
    def test_run_merge_with_custom_column(self, mock_run_merge_job, tmp_path):
        """Test merge operation with custom required column."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        expected_result = MergeResult(total_rows=2, successful_merges=2, failed_rows=[])
        mock_run_merge_job.return_value = expected_result
        
        result = run_merge(input_file, pdf_dir, output_dir, required_column="custom_column")
        
        assert result == expected_result
        mock_run_merge_job.assert_called_once_with(
            input_file=input_file,
            pdf_dir=pdf_dir,
            output_dir=output_dir,
            required_column="custom_column",
            on_progress=None,
        )
    
    @patch('pdf_merger.core.merge_orchestrator.run_merge_job')
    def test_run_merge_exception(self, mock_run_merge_job, tmp_path):
        """Test merge operation when run_merge_job raises."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_run_merge_job.side_effect = ValueError("Processing error")
        
        with pytest.raises(ValueError, match="Processing error"):
            run_merge(input_file, pdf_dir, output_dir)


class TestRunMergeJob:
    """Test cases for run_merge_job function."""
    
    @patch('pdf_merger.core.merge_orchestrator.process_job')
    @patch('pdf_merger.core.merge_orchestrator.read_data_file')
    @patch('pdf_merger.core.merge_orchestrator.logger')
    def test_run_merge_job_success(self, mock_logger, mock_read_data, mock_process_job, tmp_path):
        """Test successful merge job."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("serial_numbers\nGRNW_123")
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        # Mock read_data_file to return row data
        mock_read_data.return_value = iter([
            {"serial_numbers": "GRNW_123"}
        ])
        
        # Mock process_job to return result
        expected_result = MergeResult(
            total_rows=1,
            successful_merges=1,
            job_id="test-job"
        )
        mock_process_job.return_value = expected_result
        
        result = run_merge_job(input_file, pdf_dir, output_dir, job_id="test-job")
        
        assert result == expected_result
        mock_read_data.assert_called_once_with(input_file)
        mock_process_job.assert_called_once()
        assert mock_logger.info.called
    
    @patch('pdf_merger.core.merge_orchestrator.read_data_file')
    @patch('pdf_merger.core.merge_orchestrator.logger')
    def test_run_merge_job_read_error(self, mock_logger, mock_read_data, tmp_path):
        """Test merge job when file reading fails."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_read_data.side_effect = Exception("File read error")
        
        result = run_merge_job(input_file, pdf_dir, output_dir, job_id="test-job")
        
        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.job_id == "test-job"
        mock_logger.error.assert_called_once()
    
    @patch('pdf_merger.core.merge_orchestrator.process_job')
    @patch('pdf_merger.core.merge_orchestrator.read_data_file')
    @patch('pdf_merger.core.merge_orchestrator.logger')
    def test_run_merge_job_with_fail_on_ambiguous(self, mock_logger, mock_read_data, mock_process_job, tmp_path):
        """Test merge job with fail_on_ambiguous parameter."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("serial_numbers\nGRNW_123")
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_read_data.return_value = iter([
            {"serial_numbers": "GRNW_123"}
        ])
        
        expected_result = MergeResult(total_rows=1, successful_merges=1)
        mock_process_job.return_value = expected_result
        
        result = run_merge_job(input_file, pdf_dir, output_dir, fail_on_ambiguous=False)
        
        assert result == expected_result
        # Verify fail_on_ambiguous was passed to process_job
        call_args = mock_process_job.call_args
        assert call_args[1]['fail_on_ambiguous'] is False
    
    @patch('pdf_merger.core.merge_orchestrator.process_job')
    @patch('pdf_merger.core.merge_orchestrator.read_data_file')
    @patch('pdf_merger.core.merge_orchestrator.logger')
    def test_run_merge_job_with_custom_column(self, mock_logger, mock_read_data, mock_process_job, tmp_path):
        """Test merge job with custom required column."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("custom_col\nGRNW_123")
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_read_data.return_value = iter([
            {"custom_col": "GRNW_123"}
        ])
        
        expected_result = MergeResult(total_rows=1, successful_merges=1)
        mock_process_job.return_value = expected_result
        
        result = run_merge_job(input_file, pdf_dir, output_dir, required_column="custom_col")
        
        assert result == expected_result
        # Verify the job was created with custom column
        mock_read_data.assert_called_once_with(input_file)
    
    @patch('pdf_merger.core.merge_orchestrator.process_job')
    @patch('pdf_merger.core.merge_orchestrator.read_data_file')
    @patch('pdf_merger.core.merge_orchestrator.logger')
    def test_run_merge_job_empty_file(self, mock_logger, mock_read_data, mock_process_job, tmp_path):
        """Test merge job with empty file."""
        input_file = tmp_path / "input.csv"
        pdf_dir = tmp_path / "pdfs"
        output_dir = tmp_path / "output"
        
        mock_read_data.return_value = iter([])
        
        expected_result = MergeResult(total_rows=0, successful_merges=0)
        mock_process_job.return_value = expected_result
        
        result = run_merge_job(input_file, pdf_dir, output_dir)
        
        assert result == expected_result
        assert result.total_rows == 0
