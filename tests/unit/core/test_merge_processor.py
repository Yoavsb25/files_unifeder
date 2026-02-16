"""
Unit tests for merge_processor module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.core.merge_processor import (
    process_row,
    process_file,
    process_row_with_models,
    process_job,
    ProcessingResult
)
from pdf_merger.utils.exceptions import PDFMergerError, InvalidFileFormatError
from pdf_merger.models import Row, MergeJob, MergeResult, RowResult, RowStatus


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


class TestProcessRow:
    """Test cases for process_row function."""
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_success(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test successful processing of a row."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Setup mocks
        mock_parse.return_value = ["GRNW_000103851", "GRNW_000103852"]
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf2 = source_folder / "GRNW_000103852.pdf"
        pdf1.write_bytes(b"fake pdf")
        pdf2.write_bytes(b"fake pdf")
        
        mock_find.side_effect = [pdf1, pdf2]
        mock_merge.return_value = True
        
        result = process_row(0, "GRNW_000103851,GRNW_000103852", source_folder, output_folder)
        
        assert result is True
        mock_parse.assert_called_once_with("GRNW_000103851,GRNW_000103852")
        assert mock_find.call_count == 2
        mock_merge.assert_called_once()
    
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_no_filenames(self, mock_parse, tmp_path):
        """Test processing row with no filenames."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = []
        
        result = process_row(0, "", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_no_pdfs_found(self, mock_parse, mock_find, tmp_path):
        """Test processing row when no PDFs are found."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        mock_find.return_value = None
        
        result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_merge_fails(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test processing row when merge fails."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf1.write_bytes(b"fake pdf")
        mock_find.return_value = pdf1
        mock_merge.return_value = False
        
        result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_partial_pdfs_found(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test processing row when only some PDFs are found."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851", "GRNW_000103852"]
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf1.write_bytes(b"fake pdf")
        mock_find.side_effect = [pdf1, None]  # Second PDF not found
        mock_merge.return_value = True
        
        result = process_row(0, "GRNW_000103851,GRNW_000103852", source_folder, output_folder)
        
        assert result is True  # Should still succeed if at least one PDF is found
        mock_merge.assert_called_once()


class TestProcessFile:
    """Test cases for process_file function."""
    
    @patch('pdf_merger.core.merge_processor.process_job')
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_success(self, mock_read, mock_process_job, tmp_path):
        """Test successful processing of a file."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        # Mock file reading
        mock_read.return_value = iter([
            {"serial_numbers": "GRNW_000103851"},
            {"serial_numbers": "GRNW_000103852"},
            {"serial_numbers": "GRNW_000103853"}
        ])
        
        # Mock process_job to return successful result
        from pdf_merger.models import MergeResult
        mock_result = MergeResult(
            total_rows=3,
            successful_merges=3,
            failed_rows=[],
            skipped_rows=[]
        )
        mock_process_job.return_value = mock_result
        
        result = process_file(file_path, source_folder, output_folder)
        
        assert result.total_rows == 3
        assert result.successful_merges == 3
        assert result.failed_rows == []
        # output_folder is created by process_job, but we're mocking it, so check if it would be created
        # The actual folder creation happens in process_job, so we can't assert it exists when mocked
    
    @patch('pdf_merger.core.merge_processor.process_job')
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_with_failures(self, mock_read, mock_process_job, tmp_path):
        """Test processing file with some row failures."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([
            {"serial_numbers": "GRNW_000103851"},
            {"serial_numbers": "GRNW_000103852"},
            {"serial_numbers": "GRNW_000103853"}
        ])
        
        # Mock process_job to return result with failures
        from pdf_merger.models import MergeResult
        mock_result = MergeResult(
            total_rows=3,
            successful_merges=2,
            failed_rows=[2],  # 1-indexed
            skipped_rows=[]
        )
        mock_process_job.return_value = mock_result
        
        result = process_file(file_path, source_folder, output_folder)
        
        assert result.total_rows == 3
        assert result.successful_merges == 2
        assert result.failed_rows == [2]  # 1-indexed
    
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_empty_file(self, mock_read, tmp_path):
        """Test processing an empty file."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([])
        
        result = process_file(file_path, source_folder, output_folder)
        
        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.failed_rows == []
    
    @patch('pdf_merger.core.merge_processor.process_job')
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_missing_column(self, mock_read, mock_process_job, tmp_path):
        """Test processing file with missing serial_numbers column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([
            {"other_column": "value"},
            {"serial_numbers": "GRNW_000103851"}
        ])
        
        # Mock process_job to return result with one failure (first row has no serial_numbers)
        from pdf_merger.models import MergeResult
        mock_result = MergeResult(
            total_rows=2,
            successful_merges=1,
            failed_rows=[1],  # First row (1-indexed) failed
            skipped_rows=[]
        )
        mock_process_job.return_value = mock_result
        
        result = process_file(file_path, source_folder, output_folder)
        
        # First row should fail (no serial_numbers), second should succeed if PDF is found
        assert result.total_rows == 2
        # First row fails because no serial_numbers, second succeeds
        assert 1 in result.failed_rows  # First row definitely failed
        assert result.successful_merges == 1  # Second row succeeds
    
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_read_error(self, mock_read, tmp_path):
        """Test processing file when read_data_file raises an error."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.side_effect = InvalidFileFormatError("Read error")
        
        result = process_file(file_path, source_folder, output_folder)
        
        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.failed_rows == []
    
    @patch('pdf_merger.core.merge_processor.process_job')
    @patch('pdf_merger.core.merge_processor.read_data_file')
    def test_process_file_custom_column(self, mock_read, mock_process_job, tmp_path):
        """Test processing file with custom required column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([
            {"custom_column": "GRNW_000103851"}
        ])
        
        # Mock process_job to return successful result
        from pdf_merger.models import MergeResult
        mock_result = MergeResult(
            total_rows=1,
            successful_merges=1,
            failed_rows=[],
            skipped_rows=[]
        )
        mock_process_job.return_value = mock_result
        
        result = process_file(file_path, source_folder, output_folder, required_column="custom_column")
        
        assert result.total_rows == 1
        # Verify process_job was called
        mock_process_job.assert_called_once()
        # Verify the job was created with the custom column
        call_args = mock_process_job.call_args
        job = call_args[0][0]
        assert job.required_column == "custom_column"
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    @patch('pdf_merger.core.merge_processor.validate_serial_number')
    @patch('pdf_merger.core.merge_processor.logger')
    def test_process_row_invalid_serial_numbers(self, mock_logger, mock_validate, mock_parse, mock_find, mock_merge, tmp_path):
        """Test processing row with invalid serial numbers logs warnings but continues."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Setup: some valid, some invalid serial numbers
        mock_parse.return_value = ["GRNW_000103851", "INVALID_123", "grnw_000103852"]
        mock_validate.side_effect = [True, False, True]  # Second one is invalid
        
        pdf1 = source_folder / "GRNW_000103851.pdf"
        pdf2 = source_folder / "grnw_000103852.pdf"
        pdf1.write_bytes(b"fake pdf")
        pdf2.write_bytes(b"fake pdf")
        
        mock_find.side_effect = [pdf1, None, pdf2]
        mock_merge.return_value = True
        
        result = process_row(0, "GRNW_000103851,INVALID_123,grnw_000103852", source_folder, output_folder)
        
        # Should still succeed
        assert result is True
        
        # Should log warnings about invalid serial numbers
        assert mock_logger.warning.called
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("Invalid serial number format" in str(call) for call in warning_calls)
    
    @patch('pdf_merger.core.merge_processor.read_data_file')
    @patch('pdf_merger.core.merge_processor.logger')
    def test_process_file_unexpected_exception(self, mock_logger, mock_read, tmp_path):
        """Test processing file when an unexpected exception occurs."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        # Make read_data_file raise an unexpected exception
        mock_read.side_effect = RuntimeError("Unexpected error")
        
        result = process_file(file_path, source_folder, output_folder)
        
        # Should return a result with zero rows
        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.failed_rows == []
        
        # Should log the error
        assert mock_logger.error.called
        error_calls = [str(call) for call in mock_logger.error.call_args_list]
        assert any("Error reading file" in str(call) for call in error_calls)


class TestProcessRowWithExcel:
    """Test cases for process_row function with Excel file support."""
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_with_excel_file(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test processing row with only Excel file: Excel is skipped, no PDFs to merge, returns False."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        mock_find.return_value = excel_file
        
        result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
        mock_merge.assert_not_called()
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_mixed_pdf_and_excel(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test processing row with both PDF and Excel: Excel is skipped, only PDF is merged."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851", "GRNW_000103852"]
        pdf_file = source_folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf")
        excel_file = source_folder / "GRNW_000103852.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        mock_find.side_effect = [pdf_file, excel_file]
        mock_merge.return_value = True
        
        result = process_row(0, "GRNW_000103851,GRNW_000103852", source_folder, output_folder)
        
        assert result is True
        mock_merge.assert_called_once_with([pdf_file], output_folder / "merged_row_1.pdf")
    
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_excel_only_skipped(self, mock_parse, mock_find, tmp_path):
        """Test processing row when only Excel file exists: Excel is skipped, no PDFs, returns False."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        mock_find.return_value = excel_file
        
        result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.split_serial_numbers')
    def test_process_row_excel_skipped_no_temp_files(self, mock_parse, mock_find, mock_merge, tmp_path):
        """Test that when only Excel exists, it is skipped and no temp files are created."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        mock_find.return_value = excel_file
        
        result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
        mock_merge.assert_not_called()


class TestProcessRowWithModels:
    """Test cases for process_row_with_models function."""
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_success(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
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
    
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
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
    
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    @patch('pdf_merger.core.merge_processor.find_source_file')
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
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_partial_success(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
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
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_merge_fails(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
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
    
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_no_pdfs_after_conversion(self, mock_metrics, mock_find, mock_convert, tmp_path):
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
    
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_ambiguous_match_fail_fast(self, mock_metrics, mock_find, tmp_path):
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
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_ambiguous_match_warn(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
        """Test processing row with ambiguous match and fail_on_ambiguous=False."""
        from pdf_merger.models import Row, RowStatus
        
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        row = Row.from_raw_data(0, {"serial_numbers": "GRNW_123,GRNW_456"}, "serial_numbers")
        pdf_file = source_folder / "GRNW_123.pdf"
        pdf_file.write_bytes(b"fake pdf")
        
        # First call succeeds, second raises ValueError (ambiguous)
        mock_find.side_effect = [pdf_file, ValueError("Ambiguous match")]
        mock_convert.return_value = ([pdf_file], [])
        mock_merge.return_value = True
        mock_metrics.return_value = MagicMock()
        
        from pdf_merger.core.merge_processor import process_row_with_models
        result = process_row_with_models(row, source_folder, output_folder, fail_on_ambiguous=False)
        
        # Should continue processing with first file
        assert result.status == RowStatus.SUCCESS
        assert len(result.files_found) == 1
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_records_metrics(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
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
        result = process_row_with_models(row, source_folder, output_folder)
        
        # Verify metrics were recorded
        mock_collector.record_counter.assert_called()
        mock_collector.record_timer.assert_called()
    
    @patch('pdf_merger.core.merge_processor.merge_pdfs')
    @patch('pdf_merger.core.merge_processor._convert_excel_files_to_pdfs')
    @patch('pdf_merger.core.merge_processor.find_source_file')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_row_with_models_file_size_metric(self, mock_metrics, mock_find, mock_convert, mock_merge, tmp_path):
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
        result = process_row_with_models(row, source_folder, output_folder)
        
        # Verify gauge was recorded for file size
        gauge_calls = [call for call in mock_collector.record_gauge.call_args_list 
                      if call[0][0] == "output_file_size_mb"]
        assert len(gauge_calls) > 0


class TestProcessJob:
    """Test cases for process_job function."""
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_success(self, mock_metrics, mock_process_row, tmp_path):
        """Test successful processing of a job."""
        from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output",
            job_id="test-job"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])
        
        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.SUCCESS, output_file=tmp_path / "merged_2.pdf")
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 2
        assert result.successful_merges == 2
        assert len(result.failed_rows) == 0
        assert result.job_id == "test-job"
        assert result.total_processing_time is not None
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_with_failures(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job with some failures."""
        from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": "GRNW_456"}, "serial_numbers")
        job.add_rows([row1, row2])
        
        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.FAILED, error_message="File not found")
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 2
        assert result.successful_merges == 1
        assert result.failed_rows == [1]
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_with_skipped_rows(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job with skipped rows."""
        from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        row2 = Row.from_raw_data(1, {"serial_numbers": ""}, "serial_numbers")
        job.add_rows([row1, row2])
        
        mock_process_row.side_effect = [
            RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf"),
            RowResult(1, RowStatus.SKIPPED, error_message="No serial numbers")
        ]
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 2
        assert result.successful_merges == 1
        assert result.skipped_rows == [1]
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_pdf_merger_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when PDFMergerError occurs."""
        from pdf_merger.models import MergeJob, Row
        from pdf_merger.utils.exceptions import PDFMergerError
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
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
        failure_calls = [call for call in mock_collector.record_counter.call_args_list 
                        if len(call[0]) > 0 and call[0][0] == "jobs_failed"]
        assert len(failure_calls) > 0
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_ambiguous_match_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when ambiguous match error occurs."""
        from pdf_merger.models import MergeJob, Row
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)
        
        mock_process_row.side_effect = ValueError("Ambiguous match")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 1
        assert result.successful_merges == 0
        # Should record job failure with AmbiguousMatch error type
        failure_calls = [call for call in mock_collector.record_counter.call_args_list 
                        if len(call[0]) > 0 and call[0][0] == "jobs_failed"]
        assert len(failure_calls) > 0
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_unexpected_error(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing job when unexpected error occurs."""
        from pdf_merger.models import MergeJob, Row
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)
        
        mock_process_row.side_effect = RuntimeError("Unexpected error")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 1
        assert result.successful_merges == 0
        # Should record job failure with UnexpectedError type
        failure_calls = [call for call in mock_collector.record_counter.call_args_list 
                        if len(call[0]) > 0 and call[0][0] == "jobs_failed"]
        assert len(failure_calls) > 0
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_records_metrics(self, mock_metrics, mock_process_row, tmp_path):
        """Test that process_job records metrics."""
        from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)
        
        mock_process_row.return_value = RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        # Verify metrics were recorded
        mock_collector.record_counter.assert_any_call("jobs_started")
        mock_collector.record_counter.assert_any_call("jobs_completed")
        mock_collector.record_timer.assert_called()
        mock_collector.record_gauge.assert_called()
    
    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_fail_on_ambiguous_false(self, mock_metrics, mock_process_row, tmp_path):
        """Test process_job with fail_on_ambiguous=False."""
        from pdf_merger.models import MergeJob, Row, RowResult, RowStatus
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        row1 = Row.from_raw_data(0, {"serial_numbers": "GRNW_123"}, "serial_numbers")
        job.add_row(row1)
        
        mock_process_row.return_value = RowResult(0, RowStatus.SUCCESS, output_file=tmp_path / "merged_1.pdf")
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job, fail_on_ambiguous=False)
        
        # Verify fail_on_ambiguous was passed to process_row_with_models
        mock_process_row.assert_called_once()
        call_kwargs = mock_process_row.call_args[1]
        assert call_kwargs['fail_on_ambiguous'] is False
        # Source index is built once per job and passed to avoid repeated directory listing
        assert 'source_index' in call_kwargs
        assert isinstance(call_kwargs['source_index'], list)

    @patch('pdf_merger.core.merge_processor.process_row_with_models')
    @patch('pdf_merger.core.merge_processor.get_metrics_collector')
    def test_process_job_empty_job(self, mock_metrics, mock_process_row, tmp_path):
        """Test processing an empty job."""
        from pdf_merger.models import MergeJob
        
        job = MergeJob.create(
            input_file=tmp_path / "input.csv",
            source_folder=tmp_path / "source",
            output_folder=tmp_path / "output"
        )
        
        mock_collector = MagicMock()
        mock_metrics.return_value = mock_collector
        
        from pdf_merger.core.merge_processor import process_job
        result = process_job(job)
        
        assert result.total_rows == 0
        assert result.successful_merges == 0
        assert result.total_processing_time is not None


class TestConvertExcelFilesToPdfs:
    """Test cases for _convert_excel_files_to_pdfs function (Excel files are skipped)."""
    
    def test_convert_excel_files_to_pdfs_excel_skipped(self, tmp_path):
        """Test that Excel files are skipped and no PDF is produced."""
        from pdf_merger.core.merge_processor import _convert_excel_files_to_pdfs
        
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        output_folder = tmp_path / "output"
        output_folder.mkdir()
        
        pdf_paths, temp_files = _convert_excel_files_to_pdfs([excel_file], output_folder)
        
        assert len(pdf_paths) == 0
        assert len(temp_files) == 0
    
    def test_convert_excel_files_to_pdfs_pdf_files(self, tmp_path):
        """Test with PDF files (passed through unchanged)."""
        from pdf_merger.core.merge_processor import _convert_excel_files_to_pdfs
        
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")
        
        output_folder = tmp_path / "output"
        output_folder.mkdir()
        
        pdf_paths, temp_files = _convert_excel_files_to_pdfs([pdf_file], output_folder)
        
        assert len(pdf_paths) == 1
        assert pdf_paths[0] == pdf_file
        assert len(temp_files) == 0
    
    def test_convert_excel_files_to_pdfs_mixed_files(self, tmp_path):
        """Test with mixed PDF and Excel: only PDF is returned, Excel skipped."""
        from pdf_merger.core.merge_processor import _convert_excel_files_to_pdfs
        
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
        from pdf_merger.core.merge_processor import _cleanup_temp_files
        
        temp_file1 = tmp_path / "temp1.pdf"
        temp_file2 = tmp_path / "temp2.pdf"
        temp_file1.write_bytes(b"temp1")
        temp_file2.write_bytes(b"temp2")
        
        _cleanup_temp_files([temp_file1, temp_file2])
        
        assert not temp_file1.exists()
        assert not temp_file2.exists()
    
    def test_cleanup_temp_files_not_exists(self, tmp_path):
        """Test cleaning up non-existent files."""
        from pdf_merger.core.merge_processor import _cleanup_temp_files
        
        nonexistent = tmp_path / "nonexistent.pdf"
        
        # Should not raise error
        _cleanup_temp_files([nonexistent])
    
    @patch('pdf_merger.core.merge_processor.logger')
    def test_cleanup_temp_files_permission_error(self, mock_logger, tmp_path):
        """Test cleaning up when permission error occurs."""
        from pdf_merger.core.merge_processor import _cleanup_temp_files
        
        temp_file = tmp_path / "temp.pdf"
        temp_file.write_bytes(b"temp")
        
        with patch('pathlib.Path.unlink', side_effect=PermissionError("Permission denied")):
            _cleanup_temp_files([temp_file])
            
            mock_logger.warning.assert_called()
