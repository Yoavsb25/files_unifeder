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
    @patch('pdf_merger.processor.find_pdf_file')
    @patch('pdf_merger.processor.parse_serial_numbers')
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
    
    @patch('pdf_merger.processor.parse_serial_numbers')
    def test_process_row_no_filenames(self, mock_parse, tmp_path):
        """Test processing row with no filenames."""
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        mock_parse.return_value = []
        
        result = process_row(0, "", source_folder, output_folder)
        
        assert result is False
    
    @patch('pdf_merger.processor.find_pdf_file')
    @patch('pdf_merger.processor.parse_serial_numbers')
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
    @patch('pdf_merger.processor.find_pdf_file')
    @patch('pdf_merger.processor.parse_serial_numbers')
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
    @patch('pdf_merger.processor.find_pdf_file')
    @patch('pdf_merger.processor.parse_serial_numbers')
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
    
    @patch('pdf_merger.processor.process_row')
    @patch('pdf_merger.processor.read_data_file')
    def test_process_file_success(self, mock_read, mock_process_row, tmp_path):
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
        
        mock_process_row.return_value = True
        
        result = process_file(file_path, source_folder, output_folder)
        
        assert result.total_rows == 3
        assert result.successful_merges == 3
        assert result.failed_rows == []
        assert mock_process_row.call_count == 3
        assert output_folder.exists()
    
    @patch('pdf_merger.processor.process_row')
    @patch('pdf_merger.processor.read_data_file')
    def test_process_file_with_failures(self, mock_read, mock_process_row, tmp_path):
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
        
        mock_process_row.side_effect = [True, False, True]
        
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
    
    @patch('pdf_merger.processor.read_data_file')
    def test_process_file_missing_column(self, mock_read, tmp_path):
        """Test processing file with missing serial_numbers column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([
            {"other_column": "value"},
            {"serial_numbers": "GRNW_000103851"}
        ])
        
        result = process_file(file_path, source_folder, output_folder)
        
        # First row should fail (no serial_numbers), second should succeed
        assert result.total_rows == 2
        assert result.failed_rows == [1]  # First row failed
    
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
    
    @patch('pdf_merger.processor.process_row')
    @patch('pdf_merger.processor.read_data_file')
    def test_process_file_custom_column(self, mock_read, mock_process_row, tmp_path):
        """Test processing file with custom required column."""
        file_path = tmp_path / "data.csv"
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        
        source_folder.mkdir()
        
        mock_read.return_value = iter([
            {"custom_column": "GRNW_000103851"}
        ])
        
        mock_process_row.return_value = True
        
        result = process_file(file_path, source_folder, output_folder, required_column="custom_column")
        
        assert result.total_rows == 1
        # Verify process_row was called with the correct serial_numbers_str
        mock_process_row.assert_called_once()
        call_args = mock_process_row.call_args
        assert call_args[0][1] == "GRNW_000103851"  # Check serial_numbers_str argument
