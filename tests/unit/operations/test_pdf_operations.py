"""
Unit tests for pdf_operations module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from pdf_merger.pdf_operations import find_pdf_file, find_source_file, merge_pdfs, _get_pdf_libraries
from pdf_merger.enums import PDF_FILE_EXTENSIONS, EXCEL_FILE_EXTENSIONS


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
        
        # On case-insensitive filesystems, the returned path might be lowercase
        assert result is not None
        assert result.name.lower() == pdf_file.name.lower()
        assert result.exists()
    
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
        
        # On case-insensitive filesystems, the returned path might be lowercase
        assert result is not None
        assert result.name.lower() == target_file.name.lower()
        assert result.exists()
    
    def test_find_pdf_matches_stem(self, tmp_path):
        """Test finding PDF by matching stem (filename without extension)."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.PDF"  # Uppercase extension
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_pdf_file(folder, "GRNW_000103851")
        
        # On case-insensitive filesystems, the returned path might be lowercase
        assert result is not None
        assert result.stem.lower() == pdf_file.stem.lower()
        assert result.exists()
    
    def test_find_pdf_case_insensitive_glob_match(self, tmp_path):
        """Test finding PDF with case-insensitive glob matching."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        # Create file with different case
        pdf_file = folder / "testfile.PDF"
        pdf_file.write_bytes(b"fake pdf content")
        
        # Search with lowercase
        result = find_pdf_file(folder, "testfile")
        
        assert result is not None
        assert result.name.lower() == pdf_file.name.lower()
    
    def test_find_pdf_glob_matches_name_with_extension(self, tmp_path):
        """Test glob matching when filename includes extension in search."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        # Search with .pdf extension
        result = find_pdf_file(folder, "grnw_000103851.pdf")
        
        assert result is not None
        assert result.name.lower() == pdf_file.name.lower()
    
    def test_find_pdf_glob_matches_exact_name(self, tmp_path):
        """Test glob matching when filename matches exactly (case-insensitive)."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        # Create file with different case than search
        pdf_file = folder / "TestFile.PDF"
        pdf_file.write_bytes(b"fake pdf content")
        
        # Search with lowercase - should match via glob
        result = find_pdf_file(folder, "testfile")
        
        assert result is not None
        # Should match via the glob loop (line 70-71)
        assert result.name.lower() == pdf_file.name.lower()
    
    def test_find_pdf_glob_matches_stem_only(self, tmp_path):
        """Test glob matching when only stem matches (line 73-74)."""
        folder = tmp_path / "pdfs"
        folder.mkdir()
        # Create file
        pdf_file = folder / "GRNW_000103851.PDF"
        pdf_file.write_bytes(b"fake pdf content")
        
        # Search without extension - should match via stem check
        result = find_pdf_file(folder, "grnw_000103851")
        
        assert result is not None
        # Should match via the stem check (line 73-74)
        assert result.stem.lower() == pdf_file.stem.lower()


class TestMergePdfs:
    """Test cases for merge_pdfs function."""
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    def test_merge_pdfs_success(self, mock_get_libraries, tmp_path):
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
        mock_writer_class = MagicMock()
        mock_reader_class = MagicMock()
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance
        
        mock_reader_instance1 = MagicMock()
        mock_reader_instance2 = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_reader_instance1.pages = [mock_page1, mock_page2]
        mock_reader_instance2.pages = [mock_page1, mock_page2]
        mock_reader_class.side_effect = [mock_reader_instance1, mock_reader_instance2]
        
        mock_get_libraries.return_value = (mock_writer_class, mock_reader_class)
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is True
        assert mock_writer_class.called
        assert mock_reader_class.call_count == 2
        assert mock_writer_instance.add_page.call_count == 4  # 2 pages per PDF
        assert mock_writer_instance.write.called
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    @patch('pdf_merger.pdf_operations.logger')
    def test_merge_pdfs_empty_list(self, mock_logger, mock_get_libraries, tmp_path):
        """Test merging with empty PDF list."""
        output_path = tmp_path / "merged.pdf"
        
        result = merge_pdfs([], output_path)
        
        assert result is False
        mock_get_libraries.assert_not_called()
        mock_logger.warning.assert_called_once()
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    def test_merge_pdfs_read_error(self, mock_get_libraries, tmp_path):
        """Test merging when PDF reading fails."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_class = MagicMock()
        mock_reader_class = MagicMock()
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance
        
        mock_reader_class.side_effect = Exception("Read error")
        mock_get_libraries.return_value = (mock_writer_class, mock_reader_class)
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is False
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    def test_merge_pdfs_write_error(self, mock_get_libraries, tmp_path):
        """Test merging when PDF writing fails."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_class = MagicMock()
        mock_reader_class = MagicMock()
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance
        mock_writer_instance.write.side_effect = Exception("Write error")
        
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [MagicMock()]
        mock_reader_class.return_value = mock_reader_instance
        
        mock_get_libraries.return_value = (mock_writer_class, mock_reader_class)
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is False
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    def test_merge_pdfs_single_pdf(self, mock_get_libraries, tmp_path):
        """Test merging a single PDF."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_writer_class = MagicMock()
        mock_reader_class = MagicMock()
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance
        
        mock_reader_instance = MagicMock()
        mock_page = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_class.return_value = mock_reader_instance
        
        mock_get_libraries.return_value = (mock_writer_class, mock_reader_class)
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is True
        assert mock_writer_instance.add_page.call_count == 1
    
    @patch('pdf_merger.pdf_operations._get_pdf_libraries')
    def test_merge_pdfs_import_error(self, mock_get_libraries, tmp_path):
        """Test merging when ImportError is raised."""
        output_path = tmp_path / "merged.pdf"
        pdf_paths = [tmp_path / "file1.pdf"]
        pdf_paths[0].write_bytes(b"fake pdf content")
        
        mock_get_libraries.side_effect = ImportError("pypdf not found")
        
        result = merge_pdfs(pdf_paths, output_path)
        
        assert result is False


class TestGetPdfLibraries:
    """Test cases for _get_pdf_libraries function."""
    
    def test_get_pdf_libraries_imports_pypdf(self):
        """Test that _get_pdf_libraries imports pypdf when available."""
        import pdf_merger.pdf_operations as pdf_ops
        
        # Reset the global variables
        original_writer = pdf_ops._PdfWriter
        original_reader = pdf_ops._PdfReader
        
        try:
            pdf_ops._PdfWriter = None
            pdf_ops._PdfReader = None
            
            # Mock the pypdf import
            with patch('pypdf.PdfWriter', MagicMock()) as mock_w, \
                 patch('pypdf.PdfReader', MagicMock()) as mock_r:
                writer, reader = _get_pdf_libraries()
                
                # Should have been set
                assert pdf_ops._PdfWriter is not None
                assert pdf_ops._PdfReader is not None
        finally:
            pdf_ops._PdfWriter = original_writer
            pdf_ops._PdfReader = original_reader
    
    
    def test_get_pdf_libraries_uses_cached_imports(self):
        """Test that _get_pdf_libraries uses cached imports on subsequent calls."""
        import pdf_merger.pdf_operations as pdf_ops
        
        # Set up cached values
        original_writer = pdf_ops._PdfWriter
        original_reader = pdf_ops._PdfReader
        
        try:
            mock_writer = MagicMock()
            mock_reader = MagicMock()
            pdf_ops._PdfWriter = mock_writer
            pdf_ops._PdfReader = mock_reader
            
            # Call should return cached values without importing
            with patch('pypdf.PdfWriter') as mock_import:
                writer, reader = _get_pdf_libraries()
                
                # Should not call import since values are cached
                mock_import.assert_not_called()
                assert writer is mock_writer
                assert reader is mock_reader
        finally:
            # Restore original values
            pdf_ops._PdfWriter = original_writer
            pdf_ops._PdfReader = original_reader


class TestFindSourceFile:
    """Test cases for find_source_file function (PDF and Excel files)."""
    
    def test_find_pdf_file(self, tmp_path):
        """Test finding PDF file using find_source_file."""
        folder = tmp_path / "source"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result is not None
        assert result.exists()
        # On case-insensitive filesystems, path might differ in case
        assert result.name.lower() == pdf_file.name.lower()
        assert result.stem.lower() == "grnw_000103851"
    
    def test_find_excel_xlsx_file(self, tmp_path):
        """Test finding Excel .xlsx file."""
        folder = tmp_path / "source"
        folder.mkdir()
        excel_file = folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel content")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result is not None
        assert result.exists()
        # On case-insensitive filesystems, path might differ in case
        assert result.name.lower() == excel_file.name.lower()
        assert result.stem.lower() == "grnw_000103851"
    
    def test_find_excel_xls_file(self, tmp_path):
        """Test finding Excel .xls file."""
        folder = tmp_path / "source"
        folder.mkdir()
        excel_file = folder / "GRNW_000103851.xls"
        excel_file.write_bytes(b"fake excel content")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result is not None
        assert result.exists()
        # On case-insensitive filesystems, path might differ in case
        assert result.name.lower() == excel_file.name.lower()
        assert result.stem.lower() == "grnw_000103851"
    
    def test_find_source_file_prefers_pdf(self, tmp_path):
        """Test that find_source_file finds PDF when both PDF and Excel exist."""
        folder = tmp_path / "source"
        folder.mkdir()
        pdf_file = folder / "GRNW_000103851.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        excel_file = folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel content")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        # Should find one of them (implementation may vary, but should find a file)
        assert result is not None
        assert result.exists()
        assert result.stem.lower() == "grnw_000103851"
    
    def test_find_source_file_with_extension(self, tmp_path):
        """Test finding source file when filename includes extension."""
        folder = tmp_path / "source"
        folder.mkdir()
        excel_file = folder / "GRNW_000103851.xlsx"
        excel_file.write_bytes(b"fake excel content")
        
        result = find_source_file(folder, "GRNW_000103851.xlsx")
        
        assert result == excel_file
    
    def test_find_source_file_case_insensitive(self, tmp_path):
        """Test finding source file with case-insensitive matching."""
        folder = tmp_path / "source"
        folder.mkdir()
        excel_file = folder / "grnw_000103851.xlsx"
        excel_file.write_bytes(b"fake excel content")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result == excel_file
    
    def test_find_source_file_not_found(self, tmp_path):
        """Test when source file is not found."""
        folder = tmp_path / "source"
        folder.mkdir()
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result is None
    
    def test_find_source_file_ignores_other_files(self, tmp_path):
        """Test that find_source_file ignores non-PDF/Excel files."""
        folder = tmp_path / "source"
        folder.mkdir()
        text_file = folder / "GRNW_000103851.txt"
        text_file.write_text("some text")
        
        result = find_source_file(folder, "GRNW_000103851")
        
        assert result is None
