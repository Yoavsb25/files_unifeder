"""
Unit tests for pdf_operations module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from pdf_merger.pdf_operations import find_pdf_file, merge_pdfs
from pdf_merger.enums import PDF_FILE_EXTENSION


class TestFindPdfFile:
    """Test cases for find_pdf_file function."""
    
    def test_find_pdf_with_extension(self, tmp_path):
        """Test finding PDF file when filename includes .pdf extension."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851.pdf")
        
        assert result == pdf_file
    
    def test_find_pdf_without_extension(self, tmp_path):
        """Test finding PDF file when filename doesn't include .pdf extension."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        assert result == pdf_file
    
    def test_find_pdf_case_insensitive(self, tmp_path):
        """Test finding PDF file with case-insensitive matching."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "grnw_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        assert result == pdf_file
    
    def test_find_pdf_not_found(self, tmp_path):
        """Test when PDF file is not found."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        assert result is None
    
    def test_find_pdf_multiple_files(self, tmp_path):
        """Test finding PDF when multiple PDFs exist in folder."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        target_file = folder / "GRNW_000103851.pdf"
        target_file.write_bytes(b"fake pdf content")
        other_file = folder / "GRNW_000103852.pdf"
        other_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        assert result == target_file
    
    def test_find_pdf_matches_stem(self, tmp_path):
        """Test finding PDF by matching stem (filename without extension)."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.PDF"  # Uppercase extension
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        assert result == pdf_file


class TestMergePdfs:
    """Test cases for merge_pdfs function."""
    
    @patch('pdf_merger.pdf_operations.PdfWriter')
    @patch('pdf_merger.pdf_operations.PdfReader')
    def test_merge_pdfs_success(self, mock_pdf_reader, mock_pdf_writer, tmp_path):
        """Test successful PDF merging."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [
            tmp_path / "file1.pdf",
            tmp_path / "file2.pdf"
        ]
        
        # Create mock PDF files
        for pdf_path in pdf_paths:
            pdf_path.write_bytes(b"fake pdf content")
        
        # Setup mocks
        mock_writer_instance = MagicMock()
        mock_pdf_writer.return_value = mock_writer_instance
        
        mock_reader_instance = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is True
        assert mock_pdf_writer.called
        assert mock_pdf_reader.call_count == 2
        assert mock_writer_instance.add_page.call_count == 4  # 2 pages per PDF
        assert mock_writer_instance.write.called
    
    @patch('pdf_merger.pdf_operations.PdfWriter')
    @patch('pdf_merger.pdf_operations.PdfReader')
    def test_merge_pdfs_empty_list(self, mock_pdf_reader, mock_pdf_writer, tmp_path):
        """Test merging with empty PDF list."""
        output_path = tmp_path / "merged.pdf"
        
        result = merge_pdfs([], output_path)
        
        assert result is False
        mock_pdf_writer.assert_not_called()
        mock_pdf_reader.assert_not_called()
    
    @patch('pdf_merger.pdf_operations.PdfWriter')
    @patch('pdf_merger.pdf_operations.PdfReader')
    def test_merge_pdfs_read_error(self, mock_pdf_reader, mock_pdf_writer, tmp_path):
        """Test merging when PDF reading fails."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_instance = MagicMock()
        mock_pdf_writer.return_value = mock_writer_instance
        
        mock_pdf_reader.side_effect = Exception("Read error")
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is False
    
    @patch('pdf_merger.pdf_operations.PdfWriter')
    @patch('pdf_merger.pdf_operations.PdfReader')
    def test_merge_pdfs_write_error(self, mock_pdf_reader, mock_pdf_writer, tmp_path):
        """Test merging when PDF writing fails."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_instance = MagicMock()
        mock_pdf_writer.return_value = mock_writer_instance
        mock_writer_instance.write.side_effect = Exception("Write error")
        
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [MagicMock()]
        mock_pdf_reader.return_value = mock_reader_instance
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is False
    
    @patch('pdf_merger.pdf_operations.PdfWriter')
    @patch('pdf_merger.pdf_operations.PdfReader')
    def test_merge_pdfs_single_pdf(self, mock_pdf_reader, mock_pdf_writer, tmp_path):
        """Test merging a single PDF."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_instance = MagicMock()
        mock_pdf_writer.return_value = mock_writer_instance
        
        mock_reader_instance = MagicMock()
        mock_page = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is True
        assert mock_writer_instance.add_page.call_count == 1
