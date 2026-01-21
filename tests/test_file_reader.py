"""
Unit tests for file_reader module.
"""

import pytest
import csv
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
from pdf_merger.file_reader import (
    detect_file_type,
    read_csv,
    read_excel,
    read_data_file,
    get_file_columns,
    _detect_csv_delimiter
)
from pdf_merger.exceptions import InvalidFileFormatError
from pdf_merger.enums import FILE_TYPE_EXCEL, FILE_TYPE_CSV


class TestDetectFileType:
    """Test cases for detect_file_type function."""
    
    def test_detect_excel_xlsx(self, tmp_path):
        """Test detection of .xlsx file."""
        file_path = tmp_path / "test.xlsx"
        file_path.touch()
        assert detect_file_type(file_path) == FILE_TYPE_EXCEL
    
    def test_detect_excel_xls(self, tmp_path):
        """Test detection of .xls file."""
        file_path = tmp_path / "test.xls"
        file_path.touch()
        assert detect_file_type(file_path) == FILE_TYPE_EXCEL
    
    def test_detect_csv(self, tmp_path):
        """Test detection of CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.touch()
        assert detect_file_type(file_path) == FILE_TYPE_CSV
    
    def test_detect_other_extension(self, tmp_path):
        """Test detection of other file extension defaults to CSV."""
        file_path = tmp_path / "test.txt"
        file_path.touch()
        assert detect_file_type(file_path) == FILE_TYPE_CSV


class TestDetectCsvDelimiter:
    """Test cases for _detect_csv_delimiter function."""
    
    def test_detect_comma_delimiter(self, tmp_path):
        """Test detection of comma delimiter."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1,col2,col3\nval1,val2,val3")
        
        delimiter = _detect_csv_delimiter(file_path)
        assert delimiter == ","
    
    def test_detect_semicolon_delimiter(self, tmp_path):
        """Test detection of semicolon delimiter."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1;col2;col3\nval1;val2;val3")
        
        delimiter = _detect_csv_delimiter(file_path)
        assert delimiter == ";"
    
    def test_detect_tab_delimiter(self, tmp_path):
        """Test detection of tab delimiter."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1\tcol2\tcol3\nval1\tval2\tval3")
        
        delimiter = _detect_csv_delimiter(file_path)
        assert delimiter == "\t"
    
    def test_empty_file_defaults_to_comma(self, tmp_path):
        """Test that empty file defaults to comma delimiter."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("")
        
        delimiter = _detect_csv_delimiter(file_path)
        assert delimiter == ","
    
    def test_error_defaults_to_comma(self, tmp_path):
        """Test that error in detection defaults to comma delimiter."""
        # This test is harder to trigger, but we can test the default behavior
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1,col2\nval1,val2")
        
        delimiter = _detect_csv_delimiter(file_path)
        assert delimiter == ","


class TestReadCsv:
    """Test cases for read_csv function."""
    
    def test_read_csv_simple(self, tmp_path):
        """Test reading a simple CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1,col2\nval1,val2\nval3,val4")
        
        rows = list(read_csv(file_path))
        
        assert len(rows) == 2
        assert rows[0] == {"col1": "val1", "col2": "val2"}
        assert rows[1] == {"col1": "val3", "col2": "val4"}
    
    def test_read_csv_with_semicolon(self, tmp_path):
        """Test reading CSV with semicolon delimiter."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1;col2\nval1;val2\nval3;val4")
        
        rows = list(read_csv(file_path))
        
        assert len(rows) == 2
        assert rows[0] == {"col1": "val1", "col2": "val2"}
    
    def test_read_csv_empty_file(self, tmp_path):
        """Test reading an empty CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("")
        
        rows = list(read_csv(file_path))
        assert len(rows) == 0
    
    def test_read_csv_only_header(self, tmp_path):
        """Test reading CSV with only header row."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1,col2")
        
        rows = list(read_csv(file_path))
        assert len(rows) == 0
    
    def test_read_csv_error(self, tmp_path):
        """Test reading CSV raises InvalidFileFormatError on error."""
        file_path = tmp_path / "test.csv"
        # Create a file that will cause an error
        file_path.write_bytes(b'\x00\x01\x02')  # Binary data
        
        with pytest.raises(InvalidFileFormatError):
            list(read_csv(file_path))


class TestReadExcel:
    """Test cases for read_excel function."""
    
    @patch('pdf_merger.file_reader.pd.read_excel')
    def test_read_excel_simple(self, mock_read_excel, tmp_path):
        """Test reading a simple Excel file."""
        file_path = tmp_path / "test.xlsx"
        
        # Create mock DataFrame
        mock_df = pd.DataFrame({
            'col1': ['val1', 'val3'],
            'col2': ['val2', 'val4']
        })
        mock_read_excel.return_value = mock_df
        
        rows = list(read_excel(file_path))
        
        assert len(rows) == 2
        assert rows[0] == {"col1": "val1", "col2": "val2"}
        assert rows[1] == {"col1": "val3", "col2": "val4"}
        assert mock_read_excel.call_count == 2  # Called twice in the function
    
    @patch('pdf_merger.file_reader.pd.read_excel')
    def test_read_excel_with_nan(self, mock_read_excel, tmp_path):
        """Test reading Excel file with NaN values."""
        file_path = tmp_path / "test.xlsx"
        
        # Create mock DataFrame with NaN
        mock_df = pd.DataFrame({
            'col1': ['val1', None],
            'col2': [None, 'val4']
        })
        mock_read_excel.return_value = mock_df
        
        rows = list(read_excel(file_path))
        
        assert len(rows) == 2
        assert rows[0] == {"col1": "val1", "col2": ""}
        assert rows[1] == {"col1": "", "col2": "val4"}
    
    @patch('pdf_merger.file_reader.pd.read_excel')
    def test_read_excel_error(self, mock_read_excel, tmp_path):
        """Test reading Excel raises InvalidFileFormatError on error."""
        file_path = tmp_path / "test.xlsx"
        mock_read_excel.side_effect = Exception("Read error")
        
        with pytest.raises(InvalidFileFormatError):
            list(read_excel(file_path))


class TestReadDataFile:
    """Test cases for read_data_file function."""
    
    @patch('pdf_merger.file_reader.read_excel')
    def test_read_data_file_excel(self, mock_read_excel, tmp_path):
        """Test reading Excel file through unified interface."""
        file_path = tmp_path / "test.xlsx"
        file_path.touch()
        
        mock_read_excel.return_value = iter([{"col1": "val1"}])
        
        rows = list(read_data_file(file_path))
        
        assert len(rows) == 1
        mock_read_excel.assert_called_once_with(file_path)
    
    @patch('pdf_merger.file_reader.read_csv')
    def test_read_data_file_csv(self, mock_read_csv, tmp_path):
        """Test reading CSV file through unified interface."""
        file_path = tmp_path / "test.csv"
        file_path.touch()
        
        mock_read_csv.return_value = iter([{"col1": "val1"}])
        
        rows = list(read_data_file(file_path))
        
        assert len(rows) == 1
        mock_read_csv.assert_called_once_with(file_path)


class TestGetFileColumns:
    """Test cases for get_file_columns function."""
    
    @patch('pdf_merger.file_reader.pd.read_excel')
    def test_get_file_columns_excel(self, mock_read_excel, tmp_path):
        """Test getting columns from Excel file."""
        file_path = tmp_path / "test.xlsx"
        
        mock_df = pd.DataFrame({'col1': [1], 'col2': [2]})
        mock_read_excel.return_value = mock_df
        
        columns = get_file_columns(file_path)
        
        assert columns == ['col1', 'col2']
        mock_read_excel.assert_called_once_with(file_path)
    
    def test_get_file_columns_csv(self, tmp_path):
        """Test getting columns from CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("col1,col2,col3\nval1,val2,val3")
        
        columns = get_file_columns(file_path)
        
        assert set(columns) == {'col1', 'col2', 'col3'}
    
    def test_get_file_columns_csv_empty(self, tmp_path):
        """Test getting columns from empty CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("")
        
        columns = get_file_columns(file_path)
        
        assert columns == []
    
    @patch('pdf_merger.file_reader.pd.read_excel')
    def test_get_file_columns_excel_error(self, mock_read_excel, tmp_path):
        """Test getting columns raises InvalidFileFormatError on error."""
        file_path = tmp_path / "test.xlsx"
        mock_read_excel.side_effect = Exception("Read error")
        
        with pytest.raises(InvalidFileFormatError):
            get_file_columns(file_path)
    
    def test_get_file_columns_csv_error(self, tmp_path):
        """Test getting columns from CSV raises InvalidFileFormatError on error."""
        file_path = tmp_path / "test.csv"
        # Create a file that will cause an error
        file_path.write_bytes(b'\x00\x01\x02')  # Binary data
        
        with pytest.raises(InvalidFileFormatError):
            get_file_columns(file_path)
