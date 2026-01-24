"""
Unit tests for excel_converter module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_merger.excel_converter import convert_excel_to_pdf, _safe_str
from pdf_merger.enums import EXCEL_FILE_EXTENSIONS


class TestSafeStr:
    """Test cases for _safe_str function."""
    
    def test_safe_str_with_none(self):
        """Test _safe_str with None value."""
        assert _safe_str(None) == ''
    
    def test_safe_str_with_string(self):
        """Test _safe_str with string value."""
        assert _safe_str("test") == "test"
    
    def test_safe_str_with_number(self):
        """Test _safe_str with number value."""
        assert _safe_str(123) == "123"
    
    def test_safe_str_with_empty_string(self):
        """Test _safe_str with empty string."""
        assert _safe_str("") == ""


class TestConvertExcelToPdf:
    """Test cases for convert_excel_to_pdf function."""
    
    @patch('pdf_merger.excel_converter.SimpleDocTemplate')
    @patch('pdf_merger.excel_converter.Table')
    @patch('pdf_merger.excel_converter.openpyxl.load_workbook')
    def test_convert_excel_xlsx_success(self, mock_load_workbook, mock_table, mock_doc_template, tmp_path):
        """Test successful conversion of .xlsx file to PDF."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock workbook and sheet
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 2
        mock_sheet.max_row = 2
        mock_sheet.iter_rows.return_value = [
            [MagicMock(value="A1"), MagicMock(value="B1")],
            [MagicMock(value="A2"), MagicMock(value="B2")]
        ]
        mock_wb.active = mock_sheet
        mock_load_workbook.return_value = mock_wb
        
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is True
        mock_load_workbook.assert_called_once()
        mock_doc_template.assert_called_once()
        mock_doc.build.assert_called_once()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_file_not_found(self, mock_logger, tmp_path):
        """Test conversion when Excel file doesn't exist."""
        excel_file = tmp_path / "nonexistent.xlsx"
        output_pdf = tmp_path / "test.pdf"
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_invalid_file_type(self, mock_logger, tmp_path):
        """Test conversion when file is not an Excel file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("not excel")
        output_pdf = tmp_path / "test.pdf"
        
        result = convert_excel_to_pdf(text_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_import_error_openpyxl(self, mock_logger, tmp_path):
        """Test conversion when openpyxl is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        with patch('pdf_merger.excel_converter.openpyxl', side_effect=ImportError("openpyxl not found")):
            result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_import_error_reportlab(self, mock_logger, tmp_path):
        """Test conversion when reportlab is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        with patch('pdf_merger.excel_converter.openpyxl'):
            with patch('pdf_merger.excel_converter.SimpleDocTemplate', side_effect=ImportError("reportlab not found")):
                result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    @patch('pdf_merger.excel_converter.openpyxl.load_workbook')
    def test_convert_excel_load_error(self, mock_load_workbook, mock_logger, tmp_path):
        """Test conversion when Excel file cannot be loaded."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        mock_load_workbook.side_effect = Exception("Failed to load")
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.SimpleDocTemplate')
    @patch('pdf_merger.excel_converter.openpyxl.load_workbook')
    @patch('pathlib.Path.exists')
    def test_convert_excel_output_not_created(self, mock_exists, mock_load_workbook, mock_doc_template, tmp_path):
        """Test conversion when output PDF is not created."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock workbook
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 1
        mock_sheet.max_row = 1
        mock_sheet.iter_rows.return_value = [[MagicMock(value="A1")]]
        mock_wb.active = mock_sheet
        mock_load_workbook.return_value = mock_wb
        
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        # Mock exists() to return False for output file
        def exists_side_effect(path):
            if path == output_pdf:
                return False
            return True
        
        mock_exists.side_effect = exists_side_effect
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
