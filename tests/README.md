# Unit Tests

This directory contains comprehensive unit tests for the PDF Merger application. The tests ensure that all core functionality works correctly and help prevent regressions when making changes to the codebase.

## Overview

The test suite covers all major modules of the PDF Merger:

- **Data Parsing** - Parsing serial numbers from strings
- **Validation** - Validating files, folders, paths, and serial numbers
- **File Reading** - Reading CSV and Excel files with various delimiters
- **PDF Operations** - Finding and merging PDF files
- **Processing** - Main orchestration logic for processing files
- **Exceptions** - Custom exception classes and error handling

## Test Structure

Each test file follows a consistent structure:

```
tests/
├── __init__.py
├── test_data_parser.py      # Tests for data parsing functionality
├── test_validators.py       # Tests for validation functions
├── test_file_reader.py      # Tests for CSV/Excel file reading
├── test_pdf_operations.py   # Tests for PDF finding and merging
├── test_processor.py        # Tests for main processing logic
└── test_exceptions.py       # Tests for custom exceptions
```

## Running the Tests

### Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `pytest>=7.0.0` - The testing framework
- `pytest-cov>=4.0.0` - Coverage reporting plugin
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
pytest tests/test_data_parser.py
```

Run a specific test class:

```bash
pytest tests/test_data_parser.py::TestParseSerialNumbers
```

Run a specific test function:

```bash
pytest tests/test_data_parser.py::TestParseSerialNumbers::test_parse_single_serial_number
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

### test_data_parser.py

Tests for the `parse_serial_numbers` function:
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

### test_validators.py

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

### test_file_reader.py

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

### test_pdf_operations.py

Tests for PDF operations:
- `find_pdf_file` - Finding PDF files in a folder
- `merge_pdfs` - Merging multiple PDFs into one

**Key Test Cases:**
- Finding PDFs with and without .pdf extension
- Case-insensitive PDF matching
- Merging single and multiple PDFs
- Error handling for missing or corrupted PDFs

### test_processor.py

Tests for main processing logic:
- `ProcessingResult` - Result dataclass
- `process_row` - Processing a single row
- `process_file` - Processing an entire file

**Key Test Cases:**
- Successful row processing
- Handling missing PDFs
- Processing files with multiple rows
- Error handling and failure tracking
- Custom column names

### test_exceptions.py

Tests for custom exception classes:
- `PDFMergerError` - Base exception class
- `FileNotFoundError` - File/folder not found
- `InvalidFileFormatError` - Invalid file format
- `MissingColumnError` - Missing required column
- `PDFProcessingError` - PDF operation failures
- `ValidationError` - General validation failures

**Key Test Cases:**
- Exception creation with various parameters
- String representation of exceptions
- Path handling (Path objects and strings)
- Error message formatting

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Create a test file** following the naming convention: `test_<module_name>.py`

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
   - Example: `test_parse_serial_numbers_with_whitespace`

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

Example:

```python
from unittest.mock import patch, MagicMock

@patch('pdf_merger.module.function')
def test_something(mock_function):
    mock_function.return_value = expected_value
    # Test code
    mock_function.assert_called_once()
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test suite:

- Runs quickly (uses mocks to avoid slow I/O)
- Is deterministic (no random behavior)
- Has no external dependencies (mocks external services)
- Provides clear error messages

## Troubleshooting

### Tests fail with import errors

Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Tests fail with "ModuleNotFoundError"

Make sure you're running tests from the project root directory:
```bash
cd /path/to/files_unifeder
pytest
```

### PDF-related tests fail

Some PDF tests use mocks, but if you need to test with actual PDFs, ensure `pypdf` or `PyPDF2` is installed:
```bash
pip install pypdf
```

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
