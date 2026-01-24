"""
Unit tests for excel_converter module.
"""

import sys
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
    
    def test_convert_excel_xlsx_success(self, tmp_path):
        """Test successful conversion of .xlsx file to PDF."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Create mock modules in sys.modules
        mock_openpyxl = MagicMock()
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 2
        mock_sheet.max_row = 2
        mock_sheet.iter_rows.return_value = [
            [MagicMock(value="A1"), MagicMock(value="B1")],
            [MagicMock(value="A2"), MagicMock(value="B2")]
        ]
        mock_wb.active = mock_sheet
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        # Mock reportlab structure
        mock_doc_template = MagicMock()
        mock_table = MagicMock()
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        mock_reportlab = MagicMock()
        mock_reportlab.lib = MagicMock()
        mock_reportlab.lib.pagesizes = MagicMock()
        mock_reportlab.lib.pagesizes.letter = 'letter'
        mock_reportlab.lib.colors = MagicMock()
        mock_reportlab.lib.units = MagicMock()
        mock_reportlab.lib.units.inch = 72
        mock_reportlab.platypus = MagicMock()
        mock_reportlab.platypus.SimpleDocTemplate = mock_doc_template
        mock_reportlab.platypus.Table = mock_table
        mock_reportlab.lib.styles = MagicMock()
        mock_reportlab.lib.styles.getSampleStyleSheet = MagicMock(return_value=MagicMock())
        
        # Patch sys.modules
        with patch.dict('sys.modules', {
            'openpyxl': mock_openpyxl,
            'reportlab': mock_reportlab,
            'reportlab.lib': mock_reportlab.lib,
            'reportlab.lib.pagesizes': mock_reportlab.lib.pagesizes,
            'reportlab.lib.colors': mock_reportlab.lib.colors,
            'reportlab.lib.units': mock_reportlab.lib.units,
            'reportlab.platypus': mock_reportlab.platypus,
            'reportlab.lib.styles': mock_reportlab.lib.styles,
        }):
            # Mock Path.exists() to return True for output file after build
            original_exists = Path.exists
            with patch.object(Path, 'exists', autospec=True) as mock_exists:
                def exists_side_effect(path_instance, *args, **kwargs):
                    # Return True for output_pdf, use real exists for others
                    if path_instance == output_pdf:
                        return True
                    # For other paths, use real exists check
                    return original_exists(path_instance)
                
                mock_exists.side_effect = exists_side_effect
                
                result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is True
        mock_openpyxl.load_workbook.assert_called_once()
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
    @patch('builtins.__import__')
    def test_convert_excel_import_error_openpyxl(self, mock_import, mock_logger, tmp_path):
        """Test conversion when openpyxl is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'openpyxl':
                raise ImportError("openpyxl not found")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    @patch('builtins.__import__')
    def test_convert_excel_import_error_reportlab(self, mock_import, mock_logger, tmp_path):
        """Test conversion when reportlab is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock openpyxl
        mock_openpyxl = MagicMock()
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 1
        mock_sheet.max_row = 1
        mock_sheet.iter_rows.return_value = [[MagicMock(value="A1")]]
        mock_wb.active = mock_sheet
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'openpyxl':
                return mock_openpyxl
            elif name.startswith('reportlab'):
                raise ImportError("reportlab not found")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_load_error(self, mock_logger, tmp_path):
        """Test conversion when Excel file cannot be loaded."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock openpyxl with load_workbook that raises exception
        mock_openpyxl = MagicMock()
        mock_openpyxl.load_workbook.side_effect = Exception("Failed to load")
        
        # Mock reportlab structure
        mock_reportlab = MagicMock()
        mock_reportlab.lib = MagicMock()
        mock_reportlab.lib.pagesizes = MagicMock(letter='letter')
        mock_reportlab.lib.colors = MagicMock()
        mock_reportlab.lib.units = MagicMock(inch=72)
        mock_reportlab.platypus = MagicMock()
        mock_reportlab.lib.styles = MagicMock()
        
        with patch.dict('sys.modules', {
            'openpyxl': mock_openpyxl,
            'reportlab': mock_reportlab,
            'reportlab.lib': mock_reportlab.lib,
            'reportlab.lib.pagesizes': mock_reportlab.lib.pagesizes,
            'reportlab.lib.colors': mock_reportlab.lib.colors,
            'reportlab.lib.units': mock_reportlab.lib.units,
            'reportlab.platypus': mock_reportlab.platypus,
            'reportlab.lib.styles': mock_reportlab.lib.styles,
        }):
            result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    def test_convert_excel_output_not_created(self, tmp_path):
        """Test conversion when output PDF is not created."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock openpyxl
        mock_openpyxl = MagicMock()
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 1
        mock_sheet.max_row = 1
        mock_sheet.iter_rows.return_value = [[MagicMock(value="A1")]]
        mock_wb.active = mock_sheet
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        # Mock reportlab structure
        mock_doc_template = MagicMock()
        mock_table = MagicMock()
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        mock_reportlab = MagicMock()
        mock_reportlab.lib = MagicMock()
        mock_reportlab.lib.pagesizes = MagicMock(letter='letter')
        mock_reportlab.lib.colors = MagicMock()
        mock_reportlab.lib.units = MagicMock(inch=72)
        mock_reportlab.platypus = MagicMock()
        mock_reportlab.platypus.SimpleDocTemplate = mock_doc_template
        mock_reportlab.platypus.Table = mock_table
        mock_reportlab.lib.styles = MagicMock()
        mock_reportlab.lib.styles.getSampleStyleSheet = MagicMock(return_value=MagicMock())
        
        with patch.dict('sys.modules', {
            'openpyxl': mock_openpyxl,
            'reportlab': mock_reportlab,
            'reportlab.lib': mock_reportlab.lib,
            'reportlab.lib.pagesizes': mock_reportlab.lib.pagesizes,
            'reportlab.lib.colors': mock_reportlab.lib.colors,
            'reportlab.lib.units': mock_reportlab.lib.units,
            'reportlab.platypus': mock_reportlab.platypus,
            'reportlab.lib.styles': mock_reportlab.lib.styles,
        }):
            # Mock Path.exists() to return False for output file
            original_exists = Path.exists
            with patch.object(Path, 'exists', autospec=True) as mock_exists:
                def exists_side_effect(path_instance, *args, **kwargs):
                    # Return False for output_pdf, use real exists for others
                    if path_instance == output_pdf:
                        return False
                    # For other paths, use real exists check
                    return original_exists(path_instance)
                
                mock_exists.side_effect = exists_side_effect
                
                result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
