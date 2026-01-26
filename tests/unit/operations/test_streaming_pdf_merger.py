"""
Unit tests for streaming_pdf_merger module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.operations.streaming_pdf_merger import (
    merge_pdfs_streaming,
    get_pdf_size_mb,
    estimate_memory_usage,
    should_use_streaming
)


class TestMergePdfsStreaming:
    """Test cases for merge_pdfs_streaming function."""
    
    def test_merge_pdfs_streaming_empty_list(self, tmp_path):
        """Test merging with empty PDF list."""
        output_pdf = tmp_path / "output.pdf"
        
        result = merge_pdfs_streaming([], output_pdf)
        
        assert result is False
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_success(self, mock_logger, mock_get_libs, tmp_path):
        """Test successful streaming merge."""
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        pdf1.write_bytes(b"fake pdf1")
        pdf2.write_bytes(b"fake pdf2")
        output_pdf = tmp_path / "output.pdf"
        
        # Mock PDF libraries
        mock_writer = MagicMock()
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader.__len__ = lambda self: len(self.pages)
        
        mock_PdfWriter = MagicMock(return_value=mock_writer)
        mock_PdfReader = MagicMock(return_value=mock_reader)
        mock_get_libs.return_value = (mock_PdfWriter, mock_PdfReader)
        
        result = merge_pdfs_streaming([pdf1, pdf2], output_pdf)
        
        assert result is True
        mock_PdfReader.assert_called()
        mock_writer.add_page.assert_called()
        mock_writer.write.assert_called_once()
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_with_chunks(self, mock_logger, mock_get_libs, tmp_path):
        """Test streaming merge with chunk processing."""
        pdf1 = tmp_path / "test1.pdf"
        pdf1.write_bytes(b"fake pdf1")
        output_pdf = tmp_path / "output.pdf"
        
        # Mock PDF libraries with many pages
        mock_writer = MagicMock()
        mock_reader = MagicMock()
        # Create 25 pages
        mock_pages = [MagicMock() for _ in range(25)]
        mock_reader.pages = mock_pages
        mock_reader.__len__ = lambda self: len(self.pages)
        
        mock_PdfWriter = MagicMock(return_value=mock_writer)
        mock_PdfReader = MagicMock(return_value=mock_reader)
        mock_get_libs.return_value = (mock_PdfWriter, mock_PdfReader)
        
        result = merge_pdfs_streaming([pdf1], output_pdf, chunk_size=10)
        
        assert result is True
        # Should have added all 25 pages
        assert mock_writer.add_page.call_count == 25
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_read_error(self, mock_logger, mock_get_libs, tmp_path):
        """Test streaming merge when PDF read fails."""
        pdf1 = tmp_path / "test1.pdf"
        pdf1.write_bytes(b"fake pdf1")
        output_pdf = tmp_path / "output.pdf"
        
        # Mock PDF libraries to raise error
        mock_PdfReader = MagicMock(side_effect=Exception("Read error"))
        mock_get_libs.return_value = (MagicMock(), mock_PdfReader)
        
        result = merge_pdfs_streaming([pdf1], output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_import_error(self, mock_logger, mock_get_libs, tmp_path):
        """Test streaming merge when PDF libraries are not available."""
        pdf1 = tmp_path / "test1.pdf"
        pdf1.write_bytes(b"fake pdf1")
        output_pdf = tmp_path / "output.pdf"
        
        mock_get_libs.side_effect = ImportError("pypdf not found")
        
        result = merge_pdfs_streaming([pdf1], output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_write_error(self, mock_logger, mock_get_libs, tmp_path):
        """Test streaming merge when PDF write fails."""
        pdf1 = tmp_path / "test1.pdf"
        pdf1.write_bytes(b"fake pdf1")
        output_pdf = tmp_path / "output.pdf"
        
        # Mock PDF libraries
        mock_writer = MagicMock()
        mock_writer.write.side_effect = Exception("Write error")
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.__len__ = lambda self: len(self.pages)
        
        mock_PdfWriter = MagicMock(return_value=mock_writer)
        mock_PdfReader = MagicMock(return_value=mock_reader)
        mock_get_libs.return_value = (mock_PdfWriter, mock_PdfReader)
        
        result = merge_pdfs_streaming([pdf1], output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.operations.streaming_pdf_merger._get_pdf_libraries')
    @patch('pdf_merger.operations.streaming_pdf_merger.logger')
    def test_merge_pdfs_streaming_progress_logging(self, mock_logger, mock_get_libs, tmp_path):
        """Test that progress is logged for large files."""
        pdf1 = tmp_path / "test1.pdf"
        pdf1.write_bytes(b"fake pdf1")
        output_pdf = tmp_path / "output.pdf"
        
        # Mock PDF libraries with many pages (>100)
        mock_writer = MagicMock()
        mock_reader = MagicMock()
        # Create 150 pages
        mock_pages = [MagicMock() for _ in range(150)]
        mock_reader.pages = mock_pages
        mock_reader.__len__ = lambda self: len(self.pages)
        
        mock_PdfWriter = MagicMock(return_value=mock_writer)
        mock_PdfReader = MagicMock(return_value=mock_reader)
        mock_get_libs.return_value = (mock_PdfWriter, mock_PdfReader)
        
        result = merge_pdfs_streaming([pdf1], output_pdf, chunk_size=10)
        
        assert result is True
        # Should log progress at 50, 100, 150 pages
        mock_logger.debug.assert_called()


class TestGetPdfSizeMb:
    """Test cases for get_pdf_size_mb function."""
    
    def test_get_pdf_size_mb(self, tmp_path):
        """Test getting PDF size in megabytes."""
        # Create a file with known size (1 MB = 1024 * 1024 bytes)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"x" * (1024 * 1024))  # 1 MB
        
        size_mb = get_pdf_size_mb(pdf_file)
        
        assert abs(size_mb - 1.0) < 0.01
    
    def test_get_pdf_size_mb_small_file(self, tmp_path):
        """Test getting size of small PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"test" * 100)  # 400 bytes
        
        size_mb = get_pdf_size_mb(pdf_file)
        
        # Should be approximately 400 / (1024 * 1024) MB
        expected = 400 / (1024 * 1024)
        assert abs(size_mb - expected) < 0.0001
    
    def test_get_pdf_size_mb_not_exists(self):
        """Test getting size of non-existent PDF."""
        pdf_file = Path("/nonexistent/file.pdf")
        
        size_mb = get_pdf_size_mb(pdf_file)
        
        assert size_mb == 0.0


class TestEstimateMemoryUsage:
    """Test cases for estimate_memory_usage function."""
    
    def test_estimate_memory_usage(self, tmp_path):
        """Test estimating memory usage for PDFs."""
        # Create files with known sizes
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        # Each file is 1 MB
        pdf1.write_bytes(b"x" * (1024 * 1024))
        pdf2.write_bytes(b"x" * (1024 * 1024))
        
        estimated = estimate_memory_usage([pdf1, pdf2])
        
        # 2 MB * 2.5 = 5 MB
        assert abs(estimated - 5.0) < 0.1
    
    def test_estimate_memory_usage_empty_list(self):
        """Test estimating memory usage for empty list."""
        estimated = estimate_memory_usage([])
        
        assert estimated == 0.0
    
    def test_estimate_memory_usage_single_file(self, tmp_path):
        """Test estimating memory usage for single file."""
        pdf_file = tmp_path / "test.pdf"
        # 2 MB file
        pdf_file.write_bytes(b"x" * (2 * 1024 * 1024))
        
        estimated = estimate_memory_usage([pdf_file])
        
        # 2 MB * 2.5 = 5 MB
        assert abs(estimated - 5.0) < 0.1


class TestShouldUseStreaming:
    """Test cases for should_use_streaming function."""
    
    def test_should_use_streaming_above_threshold(self, tmp_path):
        """Test that streaming is used when above threshold."""
        # Create files totaling more than 100 MB
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        # Each file is 60 MB (total 120 MB, estimated 300 MB)
        pdf1.write_bytes(b"x" * (60 * 1024 * 1024))
        pdf2.write_bytes(b"x" * (60 * 1024 * 1024))
        
        result = should_use_streaming([pdf1, pdf2], threshold_mb=100.0)
        
        assert result is True
    
    def test_should_use_streaming_below_threshold(self, tmp_path):
        """Test that streaming is not used when below threshold."""
        # Create files totaling less than 100 MB
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        # Each file is 10 MB (total 20 MB, estimated 50 MB)
        pdf1.write_bytes(b"x" * (10 * 1024 * 1024))
        pdf2.write_bytes(b"x" * (10 * 1024 * 1024))
        
        result = should_use_streaming([pdf1, pdf2], threshold_mb=100.0)
        
        assert result is False
    
    def test_should_use_streaming_empty_list(self):
        """Test should_use_streaming with empty list."""
        result = should_use_streaming([], threshold_mb=100.0)
        
        assert result is False
    
    def test_should_use_streaming_custom_threshold(self, tmp_path):
        """Test should_use_streaming with custom threshold."""
        pdf_file = tmp_path / "test.pdf"
        # 10 MB file (estimated 25 MB)
        pdf_file.write_bytes(b"x" * (10 * 1024 * 1024))
        
        # Should use streaming with 20 MB threshold
        result1 = should_use_streaming([pdf_file], threshold_mb=20.0)
        assert result1 is True
        
        # Should not use streaming with 30 MB threshold
        result2 = should_use_streaming([pdf_file], threshold_mb=30.0)
        assert result2 is False
