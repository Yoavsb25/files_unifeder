"""
Shared fixtures for core unit tests.
"""

import pytest
from pathlib import Path

from pdf_merger.models import Row, MergeJob


@pytest.fixture
def minimal_merge_job(tmp_path):
    """Minimal MergeJob with one Row and tmp_path source/output for tests that need a job."""
    input_file = tmp_path / "input.csv"
    input_file.write_text("serial_numbers\nGRNW_1, GRNW_2")
    source_folder = tmp_path / "source"
    output_folder = tmp_path / "output"
    source_folder.mkdir()
    output_folder.mkdir()
    job = MergeJob.create(
        input_file=input_file,
        source_folder=source_folder,
        output_folder=output_folder,
        job_id="test-job",
    )
    row = Row.from_raw_data(0, {"serial_numbers": "GRNW_1, GRNW_2"}, "serial_numbers")
    job.add_row(row)
    return job
