"""
Unit tests for merge_processor module.
Tests are grouped by class.
"""

from unittest.mock import MagicMock, patch

import pytest

from pdf_merger.core.merge_processor import (
    process_job,
    process_row_with_models,
)
from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
from pdf_merger.utils.exceptions import PDFMergerError


class TestProcessRowWithModelsLegacyScenarios:
    """Test cases covering legacy process_row scenarios via process_row_with_models + Row."""

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_success(self, mock_metrics, mock_find, mock_merge, tmp_path):
        """Test successful processing of a row."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(
            0, {"serial_numbers": "GRNW_000103851,GRNW_000103852"}, "serial_numbers"
        )
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf2 = source_folder / "GRNW_000103852.pdf"
        pdf1.write_bytes(b"fake pdf")
        pdf2.write_bytes(b"fake pdf")

        mock_find.side_effect = [pdf1, pdf2]
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_success()
        assert mock_find.call_count == 2
        mock_merge.assert_called_once()

    def test_process_row_no_filenames(self, tmp_path):
        """Test processing row with no filenames."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": ""}, "serial_numbers")

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_skipped()

    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_no_pdfs_found(self, mock_metrics, mock_find, tmp_path):
        """Test processing row when no PDFs are found."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_000103851"}, "serial_numbers")
        mock_find.return_value = None
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_skipped()

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_merge_fails(self, mock_metrics, mock_find, mock_merge, tmp_path):
        """Test processing row when merge fails."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_000103851"}, "serial_numbers")
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf1.write_bytes(b"fake pdf")
        mock_find.return_value = pdf1
        mock_merge.return_value = False
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_failed()

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_partial_pdfs_found(self, mock_metrics, mock_find, mock_merge, tmp_path):
        """Test processing row when only some PDFs are found."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(
            0, {"serial_numbers": "GRNW_000103851,GRNW_000103852"}, "serial_numbers"
        )
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf1.write_bytes(b"fake pdf")
        mock_find.side_effect = [pdf1, None]
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_success() or result.status == RowStatus.PARTIAL
        mock_merge.assert_called_once()

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_invalid_serial_numbers(
        self, mock_metrics, mock_find, mock_merge, tmp_path
    ):
        """Test processing row with invalid serial numbers (Row filters them); valid ones still process."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(
            0, {"serial_numbers": "GRNW_000103851,INVALID_123,grnw_000103852"}, "serial_numbers"
        )
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf2 = source_folder / "grnw_000103852.pdf"
        pdf1.write_bytes(b"fake pdf")
        pdf2.write_bytes(b"fake pdf")

        mock_find.side_effect = [pdf1, pdf2]
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_success()
        assert mock_find.call_count == 2


class TestProcessRowWithExcel:
    """Test cases for process_row_with_models when Excel files are skipped."""

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_excel_file_is_skipped(
        self, mock_metrics, mock_find, mock_merge, tmp_path
    ):
        """Test processing row with only Excel files: row fails because there are no PDFs to merge."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_000103851"}, "serial_numbers")
        mock_find.return_value = excel_file
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_failed()
        assert "No PDF files available" in (result.error_message or "")
        mock_merge.assert_not_called()

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_mixed_pdf_and_excel(
        self, mock_metrics, mock_find, mock_merge, tmp_path
    ):
        """Test processing row with both PDF and Excel files merges only PDFs."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        pdf_file = source_folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf")
        excel_file = source_folder / "GRNW_000103852.xlsx"
        excel_file.write_bytes(b"fake excel")
        row = Row.from_raw_data(
            0, {"serial_numbers": "GRNW_000103851,GRNW_000103852"}, "serial_numbers"
        )
        mock_find.side_effect = [pdf_file, excel_file]
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_success()
        mock_merge.assert_called_once()
        merge_pdf_paths = mock_merge.call_args[0][0]
        assert merge_pdf_paths == [pdf_file]

    @patch("pdf_merger.core.row_pipeline.logger")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_logs_skipped_excel_files(
        self, mock_metrics, mock_find, mock_logger, tmp_path
    ):
        """Test processing row logs that Excel files were skipped."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_000103851"}, "serial_numbers")
        mock_find.return_value = excel_file
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_failed()
        mock_logger.warning.assert_any_call(
            "  Skipping Excel file (only PDF files are merged): GRNW_000103851.xlsx"
        )

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_pdf_still_succeeds_when_excel_present(
        self, mock_metrics, mock_find, mock_merge, tmp_path
    ):
        """Test processing row succeeds when at least one PDF exists even if Excel is skipped."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        pdf_file = source_folder / "GRNW_000103850.pdf"
        pdf_file.write_bytes(b"fake pdf")
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")

        row = Row.from_raw_data(
            0, {"serial_numbers": "GRNW_000103850,GRNW_000103851"}, "serial_numbers"
        )
        mock_find.side_effect = [pdf_file, excel_file]
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        assert result.is_success()
        mock_merge.assert_called_once()


class TestProcessRowWithModels:
    """Test cases for process_row_with_models function."""

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_success(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test successful processing with models."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        mock_find.return_value = pdf_file
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.SUCCESS
        assert result.output_file is not None
        assert len(result.files_found) == 1
        assert len(result.files_missing) == 0

    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_no_serial_numbers(self, mock_metrics, tmp_path):
        """Test processing row with no serial numbers."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": ""}, "serial_numbers")
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.SKIPPED
        assert "No valid serial numbers" in result.error_message

    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    def test_process_row_with_models_no_files_found(self, mock_find, mock_metrics, tmp_path):
        """Test processing row when no files are found."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        mock_find.return_value = None
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.SKIPPED
        assert len(result.files_missing) == 1
        assert "No source files found" in result.error_message

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_partial_success(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test processing row with partial success (some files missing)."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123,GRNW_456"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        mock_find.side_effect = [pdf_file, None]  # First found, second missing
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.PARTIAL
        assert len(result.files_missing) == 1
        assert result.files_missing[0] == "GRNW_456"

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_merge_fails(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test processing row when merge fails."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        mock_find.return_value = pdf_file
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = False
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.FAILED
        assert "Failed to merge PDFs" in result.error_message

    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_no_pdfs_after_conversion(
        self, mock_metrics, mock_find, mock_convert, tmp_path
    ):
        """Test processing row when no PDFs available after conversion."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        excel_file = source_folder / "GRNW_123.xlsx"
        excel_file.write_bytes(b"fake excel")

        mock_find.return_value = excel_file
        mock_convert.return_value = ([], [])  # No PDFs after conversion
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder)

        assert result.status == RowStatus.FAILED
        assert "No PDF files available" in result.error_message

    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_ambiguous_match_fail_fast(
        self, mock_metrics, mock_find, tmp_path
    ):
        """Test processing row with ambiguous match and fail_on_ambiguous=True."""
        from pdf_merger.models import Row

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        mock_find.side_effect = ValueError("Ambiguous match: multiple files found")
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        with pytest.raises(ValueError, match="Ambiguous match"):
            process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=True)

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_ambiguous_match_warn(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test processing row with fail_on_ambiguous=False: one file found, one missing -> PARTIAL."""
        from pdf_merger.models import Row, RowStatus

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123,GRNW_456"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        # First call returns file, second returns None (not found)
        mock_find.side_effect = [pdf_file, None]
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()

        from pdf_merger.core.merge_processor import process_row_with_models

        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)

        # One file found and merged, one missing -> PARTIAL
        assert result.status == RowStatus.PARTIAL
        assert len(result.files_found) == 1
        assert len(result.files_missing) == 1

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_records_metrics(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test that process_row_with_models records metrics."""
        from pdf_merger.models import Row

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        mock_find.return_value = pdf_file
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = True
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        from pdf_merger.core.merge_processor import process_row_with_models

        process_row_with_models(row, source_folder, output_folder)

        # Verify metrics were recorded
        mock_collector.record_counter.assert_called()
        mock_collector.record_timer.assert_called()

    @patch("pdf_merger.core.row_pipeline.merge_pdfs")
    @patch("pdf_merger.core.row_pipeline._convert_excel_files_to_pdfs")
    @patch("pdf_merger.core.row_pipeline.find_source_file")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_row_with_models_file_size_metric(
        self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path
    ):
        """Test that file size metric is recorded when available."""
        from pdf_merger.models import Row

        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()

        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")

        def create_output_file(pdf_paths, output_path, **kwargs):
            """Side effect to create output file when merge_pdfs is called."""
            # Create the output file at the path passed to merge_pdfs
            output_path.write_bytes(b"x" * (1024 * 1024))  # 1 MB
            return True

        mock_find.return_value = pdf_file
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.side_effect = create_output_file
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        from pdf_merger.core.merge_processor import process_row_with_models

        process_row_with_models(row, source_folder, output_folder)

        # Verify gauge was recorded for file size
        gauge_calls = [
            call
            for call in mock_collector.record_gauge.call_args_list
            if call[0][0] == "output_file_size_mb"
        ]
        assert len(gauge_calls) > 0


class TestProcessJob:
    """Test cases for process_job function."""

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_success(self, mock_metrics, mock_process_row, tmp_path):
        """Test successful processing of a job."""
        from pdf_merger.models import Row, RowStatus

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
            job_id="test-job",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])

        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.SUCCESS, output_file=tmp_path / "merged_2.pdf"),
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 2
        assert result.successful_merges == 2
        assert len(result.failed_rows) == 0
        assert result.job_id == "test-job"
        assert result.total_processing_time is not None

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_with_failures(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job with some failures."""
        from pdf_merger.models import Row, RowStatus

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])

        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.FAILED, error_message="File not found"),
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 2
        assert result.successful_merges == 1
        assert result.failed_rows == [1]

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_with_skipped_rows(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job with skipped rows."""
        from pdf_merger.models import Row, RowStatus

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": ""}, "serial_numbers")
        job.add_rows([row1, row2])

        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.SKIPPED, error_message="No serial numbers"),
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 2
        assert result.successful_merges == 1
        assert result.skipped_rows == [1]

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_pdf_merger_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when PDFMergerError occurs."""
        from pdf_merger.models import Row

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)

        mock_process_row.side_effect = PDFMergerError("Processing error")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        from pdf_merger.core.merge_processor import process_job

        result = process_job(job)

        assert result.total_rows == 1
        assert result.successful_merges == 0
        mock_collector.record_counter.assert_called()
        # Should record job failure with error type
        failure_calls = [
            call
            for call in mock_collector.record_counter.call_args_list
            if len(call[0]) > 0 and call[0][0] == "jobs_failed"
        ]
        assert len(failure_calls) > 0

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_ambiguous_match_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when ambiguous match error occurs."""
        from pdf_merger.models import Row

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)

        mock_process_row.side_effect = ValueError("Ambiguous match")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 1
        assert result.successful_merges == 0
        # Should record job failure with AmbiguousMatch error type
        failure_calls = [
            call
            for call in mock_collector.record_counter.call_args_list
            if len(call[0]) > 0 and call[0][0] == "jobs_failed"
        ]
        assert len(failure_calls) > 0

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_unexpected_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when unexpected error occurs."""
        from pdf_merger.models import Row

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)

        mock_process_row.side_effect = RuntimeError("Unexpected error")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 1
        assert result.successful_merges == 0
        # Should record job failure with UnexpectedError type
        failure_calls = [
            call
            for call in mock_collector.record_counter.call_args_list
            if len(call[0]) > 0 and call[0][0] == "jobs_failed"
        ]
        assert len(failure_calls) > 0

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_records_metrics(self, mock_metrics, mock_process_row, tmp_path):
        """Test that process_job records metrics."""
        from pdf_merger.models import Row, RowStatus

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)

        mock_process_row.return_value = RowResult(
            0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"
        )
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        process_job(job)

        # Verify metrics were recorded
        mock_collector.record_counter.assert_any_call("jobs_started")
        mock_collector.record_counter.assert_any_call("jobs_completed")
        mock_collector.record_timer.assert_called()
        mock_collector.record_gauge.assert_called()

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_fail_on_ambiguous_false(self, mock_metrics, mock_process_row, tmp_path):
        """Test process_job with fail_on_ambiguous=False."""
        from pdf_merger.models import Row, RowStatus

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)

        mock_process_row.return_value = RowResult(
            0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"
        )
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        process_job(job, fail_on_ambiguous=False)

        # Verify fail_on_ambiguous was passed to process_row_with_models
        mock_process_row.assert_called_once()
        call_kwargs = mock_process_row.call_args[1]
        assert call_kwargs["fail_on_ambiguous"] is False

    @patch("pdf_merger.core.merge_processor.process_row_with_models")
    @patch("pdf_merger.core.merge_processor.get_metrics_collector")
    def test_process_job_empty_job(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing an empty job."""

        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
        )

        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector

        result = process_job(job)

        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.total_processing_time is not None


class TestConvertExcelFilesToPdfs:
    """Test cases for _convert_excel_files_to_pdfs function."""

    def test_convert_excel_files_to_pdfs_skips_excel(self, tmp_path):
        """Test Excel files are skipped and no temp files are created."""
        from pdf_merger.core.row_pipeline import _convert_excel_files_to_pdfs

        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel")

        output_folder = tmp_path / "output"
        output_folder.mkdir()

        pdf_paths, temp_files = _convert_excel_files_to_pdfs([excel_file], output_folder)

        assert len(pdf_paths) == 0
        assert len(temp_files) == 0

    def test_convert_excel_files_to_pdfs_pdf_files(self, tmp_path):
        """Test with PDF files (should not convert)."""
        from pdf_merger.core.row_pipeline import _convert_excel_files_to_pdfs

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")

        output_folder = tmp_path / "output"
        output_folder.mkdir()

        pdf_paths, temp_files = _convert_excel_files_to_pdfs([pdf_file], output_folder)

        assert len(pdf_paths) == 1
        assert pdf_paths[0] == pdf_file
        assert len(temp_files) == 0

    def test_convert_excel_files_to_pdfs_mixed_files(self, tmp_path):
        """Test with mixed PDF and Excel files: only PDFs are kept."""
        from pdf_merger.core.row_pipeline import _convert_excel_files_to_pdfs

        pdf_file = tmp_path / "test1.pdf"
        pdf_file.write_bytes(b"fake pdf")
        excel_file = tmp_path / "test2.xlsx"
        excel_file.write_bytes(b"fake excel")

        output_folder = tmp_path / "output"
        output_folder.mkdir()

        pdf_paths, temp_files = _convert_excel_files_to_pdfs([pdf_file, excel_file], output_folder)

        assert len(pdf_paths) == 1
        assert pdf_paths[0] == pdf_file
        assert len(temp_files) == 0


class TestCleanupTempFiles:
    """Test cases for _cleanup_temp_files function."""

    def test_cleanup_temp_files_success(self, tmp_path):
        """Test successfully cleaning up temp files."""
        from pdf_merger.core.row_pipeline import _cleanup_temp_files

        temp_file1 = tmp_path / "temp1.pdf"
        temp_file2 = tmp_path / "temp2.pdf"
        temp_file1.write_bytes(b"temp1")
        temp_file2.write_bytes(b"temp2")

        _cleanup_temp_files([temp_file1, temp_file2])

        assert not temp_file1.exists()
        assert not temp_file2.exists()

    def test_cleanup_temp_files_not_exists(self, tmp_path):
        """Test cleaning up non-existent files."""
        from pdf_merger.core.row_pipeline import _cleanup_temp_files

        nonexistent = tmp_path / "nonexistent.pdf"

        # Should not raise error
        _cleanup_temp_files([nonexistent])

    @patch("pdf_merger.core.row_pipeline.logger")
    def test_cleanup_temp_files_permission_error(self, mock_logger, tmp_path):
        """Test cleaning up when permission error occurs."""
        from pdf_merger.core.row_pipeline import _cleanup_temp_files

        temp_file = tmp_path / "temp.pdf"
        temp_file.write_bytes(b"temp")

        with patch("pathlib.Path.unlink", side_effect=PermissionError("Permission denied")):
            _cleanup_temp_files([temp_file])

            mock_logger.warning.assert_called()
