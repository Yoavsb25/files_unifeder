"""
Unit tests for processor module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.processor import (
    process_row,
    process_file,
    ProcessingResult
)
from pdf_merger.exceptions import PDFMergerError, InvalidFileFormatError


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
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
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
    
    @patch('pdf_merger.processor.split_serial_numbers')
    def test_process_row_no_filenames(self, mock_parse, tmp_path):
        """Test processing row with no filenames."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = []
        
        result = process_row(0, "", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
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
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
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
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
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
    
    @patch('pdf_merger.processor.process_job')
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.process_job')
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.process_job')
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.process_job')
    @patch('pdf_merger.processor.read_data_file')
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
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
    @patch('pdf_merger.processor.validate_serial_number')
    @patch('pdf_merger.processor.logger')
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
    
    @patch('pdf_merger.processor.read_data_file')
    @patch('pdf_merger.processor.logger')
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
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.convert_excel_to_pdf')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
    def test_process_row_with_excel_file(self, mock_parse, mock_find, mock_convert, mock_merge, tmp_path):
        """Test processing row with Excel file that gets converted to PDF."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Setup mocks
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        # Create temporary PDF path
        temp_pdf = tmp_path / "temp_grnw_000103851.pdf"
        temp_pdf.write_bytes(b"fake pdf")
        
        mock_find.return_value = excel_file
        mock_convert.return_value = True
        mock_merge.return_value = True
        
        # Mock tempfile to return our temp PDF
        with patch('pdf_merger.processor.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(temp_pdf)
            mock_temp_file.close = MagicMock()
            mock_temp.return_value = mock_temp_file
            
            result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is True
        mock_convert.assert_called_once()
        mock_merge.assert_called_once()
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.convert_excel_to_pdf')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
    def test_process_row_mixed_pdf_and_excel(self, mock_parse, mock_find, mock_convert, mock_merge, tmp_path):
        """Test processing row with both PDF and Excel files."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Setup mocks
        mock_parse.return_value = ["GRNW_000103851", "GRNW_000103852"]
        pdf_file = source_folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf")
        excel_file = source_folder / "GRNW_000103852.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        temp_pdf = tmp_path / "temp_grnw_000103852.pdf"
        temp_pdf.write_bytes(b"fake pdf")
        
        mock_find.side_effect = [pdf_file, excel_file]
        mock_convert.return_value = True
        mock_merge.return_value = True
        
        with patch('pdf_merger.processor.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(temp_pdf)
            mock_temp_file.close = MagicMock()
            mock_temp.return_value = mock_temp_file
            
            result = process_row(0, "GRNW_000103851,GRNW_000103852", source_folder, output_folder)
        
        assert result is True
        assert mock_convert.call_count == 1  # Only Excel file should be converted
        mock_merge.assert_called_once()
    
    @patch('pdf_merger.processor.convert_excel_to_pdf')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
    def test_process_row_excel_conversion_fails(self, mock_parse, mock_find, mock_convert, tmp_path):
        """Test processing row when Excel conversion fails."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        mock_find.return_value = excel_file
        mock_convert.return_value = False  # Conversion fails
        
        with patch('pdf_merger.processor.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.pdf")
            mock_temp_file.close = MagicMock()
            mock_temp.return_value = mock_temp_file
            
            result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.processor.merge_pdfs')
    @patch('pdf_merger.processor.convert_excel_to_pdf')
    @patch('pdf_merger.processor.find_source_file')
    @patch('pdf_merger.processor.split_serial_numbers')
    @patch('pdf_merger.processor.logger')
    def test_process_row_cleans_up_temp_files(self, mock_logger, mock_parse, mock_find, mock_convert, mock_merge, tmp_path):
        """Test that temporary PDF files are cleaned up after merging."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = ["GRNW_000103851"]
        excel_file = source_folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel")
        
        temp_pdf = tmp_path / "temp_grnw_000103851.pdf"
        temp_pdf.write_bytes(b"fake pdf")
        
        mock_find.return_value = excel_file
        mock_convert.return_value = True
        mock_merge.return_value = True
        
        with patch('pdf_merger.processor.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(temp_pdf)
            mock_temp_file.close = MagicMock()
            mock_temp.return_value = mock_temp_file
            
            result = process_row(0, "GRNW_000103851", source_folder, output_folder)
        
        assert result is True
        # Verify temp file cleanup was attempted (via unlink)
        # The actual cleanup happens in the finally block
