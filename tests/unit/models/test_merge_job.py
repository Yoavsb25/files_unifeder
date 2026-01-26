"""
Unit tests for merge_job module.
"""

import pytest
from pathlib import Path
from pdf_merger.models.merge_job import MergeJob
from pdf_merger.models.row import Row
from pdf_merger.constants import Constants


class TestMergeJob:
    """Test cases for MergeJob class."""
    
    def test_merge_job_create(self, tmp_path):
        """Test creating a MergeJob."""
        input_file = tmp_path / "input.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        job = MergeJob.create(
            input_file=input_file,
            source_folder=source_folder,
            output_folder=output_folder
        )
        
        assert job.input_file == input_file
        assert job.source_folder == source_folder
        assert job.output_folder == output_folder
        assert job.required_column == Constants.DEFAULT_SERIAL_NUMBERS_COLUMN
        assert len(job.rows) == 0
        assert job.job_id is None
        assert job.metadata == {}
    
    def test_merge_job_create_with_job_id(self, tmp_path):
        """Test creating a MergeJob with job_id."""
        input_file = tmp_path / "input.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        job = MergeJob.create(
            input_file=input_file,
            source_folder=source_folder,
            output_folder=output_folder,
            job_id="job-123"
        )
        
        assert job.job_id == "job-123"
    
    def test_merge_job_create_with_metadata(self, tmp_path):
        """Test creating a MergeJob with metadata."""
        input_file = tmp_path / "input.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        metadata = {"key": "value"}
        
        job = MergeJob.create(
            input_file=input_file,
            source_folder=source_folder,
            output_folder=output_folder,
            metadata=metadata
        )
        
        assert job.metadata == metadata
    
    def test_merge_job_create_with_custom_column(self, tmp_path):
        """Test creating a MergeJob with custom required column."""
        input_file = tmp_path / "input.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        job = MergeJob.create(
            input_file=input_file,
            source_folder=source_folder,
            output_folder=output_folder,
            required_column="custom_column"
        )
        
        assert job.required_column == "custom_column"
    
    def test_add_row(self, tmp_path):
        """Test adding a single row."""
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row)
        
        assert len(job.rows) == 1
        assert job.rows[0] == row
    
    def test_add_rows(self, tmp_path):
        """Test adding multiple rows."""
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        row3 = Row.from_raw_data(2, {"serial_numbers": "GRNW_789"}, "serial_numbers")
        
        job.add_rows([row1, row2, row3])
        
        assert len(job.rows) == 3
        assert job.rows[0] == row1
        assert job.rows[1] == row2
        assert job.rows[2] == row3
    
    def test_get_total_rows(self, tmp_path):
        """Test getting total number of rows."""
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        assert job.get_total_rows() == 0
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])
        
        assert job.get_total_rows() == 2
    
    def test_get_rows_with_serial_numbers(self, tmp_path):
        """Test getting rows with valid serial numbers."""
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": ""}, "serial_numbers")  # Empty
        row3 = Row.from_raw_data(2, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        
        job.add_rows([row1, row2, row3])
        
        rows_with_serial = job.get_rows_with_serial_numbers()
        
        assert len(rows_with_serial) == 2
        assert row1 in rows_with_serial
        assert row3 in rows_with_serial
        assert row2 not in rows_with_serial
    
    def test_merge_job_str(self, tmp_path):
        """Test MergeJob string representation."""
        input_file = tmp_path / "input.csv"
        job = MergeJob.create(
            input_file=input_file,
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])
        
        str_repr = str(job)
        assert "input.csv" in str_repr
        assert "rows=2" in str_repr
