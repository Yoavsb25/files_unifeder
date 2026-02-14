"""
Unit tests for job_loader module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from pdf_merger.core.job_loader import load_job_from_file
from pdf_merger.utils.exceptions import JobLoadError


class TestLoadJobFromFile:
    """Test cases for load_job_from_file."""

    @patch('pdf_merger.core.job_loader.read_data_file')
    def test_raises_job_load_error_on_unexpected_exception(self, mock_read_data, tmp_path):
        """When read_data_file raises an unexpected exception, load_job_from_file raises JobLoadError."""
        input_file = tmp_path / "input.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        mock_read_data.side_effect = RuntimeError("Unexpected parse failure")

        with pytest.raises(JobLoadError) as exc_info:
            load_job_from_file(
                input_file=input_file,
                source_folder=source_folder,
                output_folder=output_folder,
                required_column="serial_numbers",
            )

        assert "Unexpected parse failure" in str(exc_info.value)
        assert exc_info.value.path == input_file
        assert exc_info.value.cause is mock_read_data.side_effect
