"""
Unit tests for excel_converter module.
"""

import pytest
import sys
import warnings
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
        
        # Mock workbook and sheet
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 2
        mock_sheet.max_row = 2
        # iter_rows with values_only=True returns tuples directly
        mock_sheet.iter_rows.return_value = [
            ("A1", "B1"),
            ("A2", "B2")
        ]
        mock_wb.active = mock_sheet
        
        # Mock openpyxl module
        mock_openpyxl = MagicMock()
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        # Mock reportlab modules
        mock_letter = (612, 792)
        mock_A4 = (595, 842)
        mock_landscape = lambda x: x
        
        mock_colors = MagicMock()
        mock_colors.white = 'white'
        mock_colors.black = 'black'
        mock_colors.whitesmoke = 'whitesmoke'
        mock_colors.HexColor = MagicMock(return_value='hexcolor')
        
        mock_inch = 72
        
        mock_table = MagicMock()
        mock_table_style = MagicMock()
        mock_paragraph = MagicMock()
        mock_spacer = MagicMock()
        mock_page_break = MagicMock()
        mock_doc_template = MagicMock()
        mock_doc = MagicMock()
        # Make build() create the output file to simulate successful PDF creation
        def build_side_effect(*args, **kwargs):
            output_pdf.touch()
        mock_doc.build.side_effect = build_side_effect
        mock_doc_template.return_value = mock_doc
        
        mock_styles = MagicMock()
        mock_styles.getSampleStyleSheet.return_value = MagicMock()
        
        # Create mock modules
        mock_pagesizes = MagicMock()
        mock_pagesizes.letter = mock_letter
        mock_pagesizes.A4 = mock_A4
        mock_pagesizes.landscape = mock_landscape
        
        mock_lib = MagicMock()
        mock_lib.colors = mock_colors
        mock_lib.units = MagicMock(inch=mock_inch)
        
        mock_platypus = MagicMock()
        mock_platypus.Table = mock_table
        mock_platypus.TableStyle = mock_table_style
        mock_platypus.Paragraph = mock_paragraph
        mock_platypus.Spacer = mock_spacer
        mock_platypus.PageBreak = mock_page_break
        mock_platypus.SimpleDocTemplate = mock_doc_template
        
        # Setup sys.modules
        with patch.dict('sys.modules', {
            'openpyxl': mock_openpyxl,
            'reportlab': MagicMock(),
            'reportlab.lib': mock_lib,
            'reportlab.lib.pagesizes': mock_pagesizes,
            'reportlab.lib.units': mock_lib.units,
            'reportlab.platypus': mock_platypus,
            'reportlab.lib.styles': mock_styles,
        }):
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
    def test_convert_excel_import_error_openpyxl(self, mock_logger, tmp_path):
        """Test conversion when openpyxl is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock import to raise ImportError
        def import_side_effect(name, *args, **kwargs):
            if name == 'openpyxl':
                raise ImportError("openpyxl not found")
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=import_side_effect):
            result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_import_error_reportlab(self, mock_logger, tmp_path):
        """Test conversion when reportlab is not installed."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock openpyxl import to succeed
        mock_openpyxl = MagicMock()
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 1
        mock_sheet.max_row = 1
        mock_sheet.iter_rows.return_value = [[MagicMock(value="A1")]]
        mock_wb.active = mock_sheet
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        # Mock import to raise ImportError for reportlab
        def import_side_effect(name, *args, **kwargs):
            if name == 'reportlab.lib.pagesizes' or name == 'reportlab':
                raise ImportError("reportlab not found")
            if name == 'openpyxl':
                return mock_openpyxl
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=import_side_effect):
            result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('pdf_merger.excel_converter.logger')
    def test_convert_excel_load_error(self, mock_logger, tmp_path):
        """Test conversion when Excel file cannot be loaded."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock openpyxl import
        mock_openpyxl = MagicMock()
        mock_openpyxl.load_workbook.side_effect = Exception("Failed to load")
        
        # Suppress deprecation warning from importlib when mocking modules
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, 
                                  message=".*load_module.*")
            with patch.dict('sys.modules', {'openpyxl': mock_openpyxl}):
                result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
        mock_logger.error.assert_called()
    
    def test_convert_excel_output_not_created(self, tmp_path):
        """Test conversion when output PDF is not created."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"fake excel content")
        output_pdf = tmp_path / "test.pdf"
        
        # Mock workbook
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_column = 1
        mock_sheet.max_row = 1
        # iter_rows with values_only=True returns tuples directly
        mock_sheet.iter_rows.return_value = [("A1",)]
        mock_wb.active = mock_sheet
        
        # Mock openpyxl module
        mock_openpyxl = MagicMock()
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        # Mock reportlab modules
        mock_letter = (612, 792)
        mock_landscape = lambda x: x
        
        mock_colors = MagicMock()
        mock_colors.white = 'white'
        mock_colors.black = 'black'
        mock_colors.whitesmoke = 'whitesmoke'
        mock_colors.HexColor = MagicMock(return_value='hexcolor')
        
        mock_inch = 72
        
        mock_table = MagicMock()
        mock_table_style = MagicMock()
        mock_paragraph = MagicMock()
        mock_spacer = MagicMock()
        mock_page_break = MagicMock()
        mock_doc_template = MagicMock()
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        mock_styles = MagicMock()
        mock_styles.getSampleStyleSheet.return_value = MagicMock()
        
        # Create mock modules
        mock_pagesizes = MagicMock()
        mock_pagesizes.letter = mock_letter
        mock_pagesizes.landscape = mock_landscape
        
        mock_lib = MagicMock()
        mock_lib.colors = mock_colors
        mock_lib.units = MagicMock(inch=mock_inch)
        
        mock_platypus = MagicMock()
        mock_platypus.Table = mock_table
        mock_platypus.TableStyle = mock_table_style
        mock_platypus.Paragraph = mock_paragraph
        mock_platypus.Spacer = mock_spacer
        mock_platypus.PageBreak = mock_page_break
        mock_platypus.SimpleDocTemplate = mock_doc_template
        
        # Setup sys.modules
        with patch.dict('sys.modules', {
            'openpyxl': mock_openpyxl,
            'reportlab': MagicMock(),
            'reportlab.lib': mock_lib,
            'reportlab.lib.pagesizes': mock_pagesizes,
            'reportlab.lib.units': mock_lib.units,
            'reportlab.platypus': mock_platypus,
            'reportlab.lib.styles': mock_styles,
        }):
            # Ensure build() doesn't create the file (it's already mocked to do nothing)
            # Patch Path.exists to return False for the output file
            original_exists = Path.exists
            
            def exists_patch(self):
                # Check if this is the output_pdf by comparing string representation
                if str(self) == str(output_pdf):
                    return False
                # For other paths, use the real exists method
                return original_exists(self)
            
            with patch.object(Path, 'exists', exists_patch):
                result = convert_excel_to_pdf(excel_file, output_pdf)
        
        assert result is False
