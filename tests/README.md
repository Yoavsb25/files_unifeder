# Unit Tests

This directory contains comprehensive unit tests for the PDF Merger application. The tests ensure that all core functionality works correctly and help prevent regressions when making changes to the codebase.

## Organization

Tests are organized into logical subdirectories by module category for better maintainability and navigation:

- **`unit/core/`** - Core business logic: merge orchestration, processing, serial number parsing, CSV/Excel reading
- **`unit/operations/`** - Operations: PDF merging, streaming PDF merging, Excel to PDF conversion
- **`unit/ui/`** - User interface components
- **`unit/licensing/`** - License management and validation
- **`unit/utils/`** - Utilities: logging, validation, path utilities, exceptions
- **`unit/config/`** - Configuration management
- **`unit/models/`** - Data models
- **`unit/matching/`** - Matching rules
- **`unit/observability/`** - Observability: metrics, telemetry, crash reporting

This organization makes it easy to:
- Find tests for specific functionality
- Run tests by category
- Maintain and extend the test suite
- Understand the codebase structure

## Overview

The test suite covers all major modules of the PDF Merger:

- **Data Parsing** - Parsing serial numbers from strings
- **Validation** - Validating files, folders, paths, and serial numbers
- **File Reading** - Reading CSV and Excel files with various delimiters
- **PDF Operations** - Finding and merging PDF files (including Excel files)
- **Excel Conversion** - Converting Excel files to PDF format
- **Processing** - Main orchestration logic for processing files
- **Exceptions** - Custom exception classes and error handling

**Current Status:** Comprehensive test coverage including Excel file support. All tests pass successfully.

## Test Structure

Tests are organized into logical subdirectories by module category:

```
tests/
├── __init__.py
├── README.md                # This file
│
└── unit/                    # Unit tests organized by category
    ├── core/                # Core business logic tests
    │   ├── test_merge_orchestrator.py    # Merge orchestration
    │   ├── test_result_reporter.py       # Result reporting
    │   ├── test_merge_processor.py        # Merge processing
    │   ├── test_csv_excel_reader.py      # CSV/Excel file reading
    │   ├── test_serial_number_parser.py  # Serial number parsing
    │   └── test_core_module_exports.py   # Core module exports
    │
    ├── operations/          # Operations tests
    │   ├── test_pdf_merger.py            # PDF merging
    │   ├── test_streaming_pdf_merger.py # Streaming PDF merging
    │   └── test_excel_to_pdf_converter.py # Excel to PDF conversion
    │
    ├── ui/                  # UI tests
    │   ├── test_app.py                  # GUI application
    │   ├── test_components.py            # UI components
    │   ├── test_handlers.py              # UI handlers
    │   ├── test_license_ui.py            # License UI
    │   └── test_ui_module_exports.py     # UI module exports
    │
    ├── licensing/           # Licensing tests
    │   ├── test_license_manager.py       # License management
    │   └── test_licensing_module_exports.py # Licensing module exports
    │
    ├── config/              # Configuration tests
    │   ├── test_config_manager.py       # Configuration management
    │   └── test_config_schema.py        # Configuration schema
    │
    ├── models/              # Data model tests
    │   ├── test_merge_job.py            # Merge job model
    │   ├── test_merge_result.py         # Merge result model
    │   └── test_row.py                  # Row model
    │
    ├── matching/            # Matching rules tests
    │   └── test_rules.py               # Matching rules
    │
    ├── observability/       # Observability tests
    │   ├── test_crash_reporting.py     # Crash reporting
    │   ├── test_metrics.py             # Metrics
    │   └── test_telemetry.py           # Telemetry
    │
    └── utils/               # Utility tests
        ├── test_exceptions.py           # Custom exceptions
        ├── test_logging_utils.py        # Logging system
        ├── test_path_utils.py           # Path utilities
        ├── test_validators.py           # Input validation
        └── test_utils_module_exports.py # Utils module exports
```

Each test file follows a consistent structure with test classes grouping related test cases.

## Running the Tests

### Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `pytest>=7.0.0` - The testing framework
- `pytest-cov>=4.0.0` - Coverage reporting plugin
- `openpyxl>=3.0.0` - Excel file reading (for Excel conversion tests)
- `reportlab>=3.6.0` - PDF generation (for Excel conversion tests)
- All other project dependencies

### Basic Usage

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/unit/core/test_serial_number_parser.py
```

Run all tests in a category:

```bash
pytest tests/unit/data/          # All data processing tests
pytest tests/unit/operations/    # All operations tests
pytest tests/unit/core/          # All core tests
```

Run a specific test class:

```bash
pytest tests/unit/core/test_serial_number_parser.py::TestSplitSerialNumbers
```

Run a specific test function:

```bash
pytest tests/unit/core/test_serial_number_parser.py::TestSplitSerialNumbers::test_split_single_serial_number
```

### Running with Coverage

Generate a coverage report:

```bash
pytest --cov=pdf_merger --cov-report=term-missing
```

Generate an HTML coverage report:

```bash
pytest --cov=pdf_merger --cov-report=html
```

The HTML report will be generated in `htmlcov/index.html`. Open it in a browser to see detailed coverage information.

## Test Details

### unit/core/test_serial_number_parser.py

Tests for the `split_serial_numbers` function:
- Parsing single and multiple serial numbers
- Handling whitespace
- Empty strings and None inputs
- Mixed case serial numbers
- Edge cases with empty elements

**Key Test Cases:**
- Single serial number parsing
- Multiple comma-separated serial numbers
- Whitespace handling
- Empty string handling
- Invalid input handling

### unit/utils/test_validators.py

Tests for validation functions:
- `validate_serial_number` - Validates serial number format (GRNW_ prefix)
- `validate_folder` - Validates folder existence and type
- `validate_file` - Validates file existence and required columns
- `validate_paths` - Validates all paths needed for processing

**Key Test Cases:**
- Valid and invalid serial number formats
- Existing and non-existent folders
- Files with and without required columns
- Complete path validation scenarios

### unit/core/test_csv_excel_reader.py

Tests for file reading operations:
- `detect_file_type` - Detecting CSV vs Excel files
- `_detect_csv_delimiter` - Auto-detecting CSV delimiters
- `read_csv` - Reading CSV files
- `read_excel` - Reading Excel files
- `read_data_file` - Unified file reading interface
- `get_file_columns` - Extracting column names

**Key Test Cases:**
- File type detection (.xlsx, .xls, .csv)
- CSV delimiter detection (comma, semicolon, tab)
- Reading CSV and Excel files
- Handling empty files
- Error handling for invalid files

### unit/operations/test_pdf_merger.py

Tests for PDF operations:
- `find_pdf_file` - Finding PDF files in a folder (backward compatibility)
- `find_source_file` - Finding PDF and Excel files in a folder
- `merge_pdfs` - Merging multiple PDFs into one

**Key Test Cases:**
- Finding PDFs with and without .pdf extension
- Finding Excel files (.xlsx, .xls)
- Case-insensitive file matching (handles case-insensitive filesystems)
- Merging single and multiple PDFs
- Error handling for missing or corrupted PDFs
- Suppressing noisy PDF read warnings

**Note:** PDF library imports are lazy-loaded (only when `merge_pdfs` is called), so tests can run without pypdf installed. Tests mock `_get_pdf_libraries()` to avoid requiring actual PDF libraries.

### unit/operations/test_excel_to_pdf_converter.py

Tests for Excel to PDF conversion:
- `convert_excel_to_pdf` - Converting Excel files to PDF format
- `_safe_str` - Safely converting values to strings

**Key Test Cases:**
- Converting .xlsx files to PDF
- Converting .xls files to PDF (note: openpyxl only supports .xlsx)
- Handling missing Excel files
- Handling invalid file types
- Error handling for import errors (openpyxl, reportlab)
- Error handling for conversion failures
- Handling empty Excel files

**Note:** Excel conversion uses openpyxl (for reading) and reportlab (for PDF generation). Tests mock these libraries to avoid requiring actual Excel files.

### unit/core/test_merge_processor.py

Tests for main processing logic:
- `ProcessingResult` - Result dataclass
- `process_row` - Processing a single row (PDF and Excel files)
- `process_file` - Processing an entire file

**Key Test Cases:**
- Successful row processing with PDF files
- Successful row processing with Excel files
- Mixed processing (PDF + Excel in same row)
- Handling missing files
- Excel to PDF conversion during processing
- Temporary file cleanup after merging
- Processing files with multiple rows
- Error handling and failure tracking
- Custom column names

### unit/utils/test_exceptions.py

Tests for custom exception classes:
- `PDFMergerError` - Base exception class
- `PDFMergerFileNotFoundError` - File/folder not found
- `InvalidFileFormatError` - Invalid file format
- `MissingColumnError` - Missing required column
- `PDFProcessingError` - PDF operation failures
- `ValidationError` - General validation failures

**Key Test Cases:**
- Exception creation with various parameters
- String representation of exceptions
- Path handling (Path objects and strings)
- Error message formatting

## Running Tests by Category

You can run tests for specific categories:

```bash
# Run all core tests (includes data processing)
pytest tests/unit/core/

# Run all operations tests
pytest tests/unit/operations/

# Run all core tests
pytest tests/unit/core/

# Run all UI tests
pytest tests/unit/ui/

# Run all licensing tests
pytest tests/unit/licensing/

# Run all utility tests
pytest tests/unit/utils/
```

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Place test file in the appropriate category directory**:
   - Core logic (orchestration, processing, parsing, reading) → `tests/unit/core/`
   - Operations (PDF merging, Excel conversion) → `tests/unit/operations/`
   - UI components → `tests/unit/ui/`
   - Licensing → `tests/unit/licensing/`
   - Utilities (logging, validation, paths, exceptions) → `tests/unit/utils/`
   - Configuration → `tests/unit/config/`
   - Models → `tests/unit/models/`
   - Matching rules → `tests/unit/matching/`
   - Observability → `tests/unit/observability/`

2. **Create a test file** following the naming convention: `test_<module_name>.py`

2. **Organize tests into classes** that group related test cases:
   ```python
   class TestNewFunction:
       """Test cases for new_function."""
       
       def test_new_function_success(self):
           """Test successful execution."""
           # Test implementation
           pass
   ```

3. **Use descriptive test names** that explain what is being tested:
   - `test_<function>_<scenario>` format
   - Example: `test_split_serial_numbers_with_whitespace`

4. **Use fixtures** for common setup:
   - `tmp_path` - For temporary files and directories
   - `unittest.mock` - For mocking external dependencies

5. **Test edge cases**:
   - Empty inputs
   - None values
   - Invalid inputs
   - Error conditions

6. **Use assertions** that provide clear failure messages:
   ```python
   assert result == expected, f"Expected {expected}, got {result}"
   ```

## Mocking

The tests use `unittest.mock` to mock external dependencies:

- **File operations** - Mocked to avoid actual file I/O in some tests
- **PDF libraries** - Mocked to avoid requiring actual PDF files
- **Pandas** - Mocked in some tests to avoid reading actual Excel files

### Basic Mocking Example

```python
from unittest.mock import patch, MagicMock

@patch('pdf_merger.module.function')
def test_something(mock_function):
    mock_function.return_value = expected_value
    # Test code
    mock_function.assert_called_once()
```

### Mocking Excel Conversion

Excel conversion uses openpyxl and reportlab. Mock these libraries in tests:

```python
from unittest.mock import patch, MagicMock

@patch('pdf_merger.excel_converter.openpyxl.load_workbook')
@patch('pdf_merger.excel_converter.SimpleDocTemplate')
def test_convert_excel(mock_doc_template, mock_load_workbook, tmp_path):
    # Setup mocks
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.max_column = 2
    mock_sheet.max_row = 2
    mock_sheet.iter_rows.return_value = [[MagicMock(value="A1")]]
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    
    # Test code
    result = convert_excel_to_pdf(excel_file, output_pdf)
    assert result is True
```

### Mocking PDF Operations

Since PDF libraries use lazy imports, mock `_get_pdf_libraries()` instead of `PdfReader`/`PdfWriter` directly:

```python
from unittest.mock import patch, MagicMock

@patch('pdf_merger.pdf_operations._get_pdf_libraries')
def test_merge_pdfs(mock_get_libraries, tmp_path):
    # Setup mock PDF classes
    mock_writer_class = MagicMock()
    mock_reader_class = MagicMock()
    mock_writer_instance = MagicMock()
    mock_writer_class.return_value = mock_writer_instance
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [MagicMock()]
    mock_reader_class.return_value = mock_reader_instance
    
    # Return tuple of (PdfWriter, PdfReader) classes
    mock_get_libraries.return_value = (mock_writer_class, mock_reader_class)
    
    # Test code
    result = merge_pdfs(pdf_paths, output_path)
    assert result is True
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test suite:

- Runs quickly (uses mocks to avoid slow I/O)
- Is deterministic (no random behavior)
- Has minimal external dependencies (lazy imports + mocks)
- Can run without pypdf installed (lazy imports allow module import)
- Provides clear error messages

**Lazy Import Benefits:**
- Tests can be collected and run even if pypdf isn't installed
- Only tests that actually call `merge_pdfs()` need pypdf (or proper mocking)
- Faster test collection (no import-time failures)

## Troubleshooting

### Tests fail with import errors

The PDF library import is now **lazy** (only imports when `merge_pdfs()` is called), so you can run most tests without installing pypdf. The module can be imported successfully even without PDF libraries installed.

However, for full functionality and to run tests that actually call `merge_pdfs()` without mocking, install all dependencies:

```bash
pip install -r requirements.txt
```

**Note:** If you see `SystemExit: 1` errors or `AttributeError: does not have the attribute 'PdfReader'`, it means:
- The code is using the old import pattern (should be fixed)
- Or tests are trying to mock `PdfReader`/`PdfWriter` directly instead of `_get_pdf_libraries()`

### Tests fail with "ModuleNotFoundError"

Make sure you're running tests from the project root directory:
```bash
cd /path/to/files_unifeder
pytest
```

### PDF-related tests fail

PDF tests use mocks by default, so they should work without pypdf installed. If you see errors about missing `PdfReader` or `PdfWriter` attributes:

1. **Check that tests mock `_get_pdf_libraries()`** - Don't mock `PdfReader`/`PdfWriter` directly
2. **For actual PDF testing** - Install pypdf if you need to test with real PDFs:
   ```bash
   pip install pypdf
   ```

The lazy import system means:
- ✅ Module can be imported without pypdf
- ✅ Tests can run without pypdf (using mocks)
- ✅ Only fails if `merge_pdfs()` is called without pypdf installed AND without mocking

## Contributing

When contributing to the codebase:

1. **Write tests first** (TDD approach) or alongside your code
2. **Ensure all tests pass** before submitting PRs
3. **Maintain or improve coverage** - aim for >80% coverage
4. **Update this README** if you add new test patterns or conventions

## Coverage Goals

The project aims for:
- **>80% code coverage** overall
- **100% coverage** for critical functions (parsing, validation)
- **>70% coverage** for utility functions

Check current coverage with:
```bash
pytest --cov=pdf_merger --cov-report=term-missing
```
