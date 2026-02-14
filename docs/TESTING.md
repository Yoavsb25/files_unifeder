# PDF Batch Merger - Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Test Categories](#test-categories)
6. [Writing New Tests](#writing-new-tests)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The PDF Batch Merger project uses **pytest** as the testing framework with comprehensive test coverage across all modules. The test suite ensures that all core functionality works correctly and helps prevent regressions when making changes to the codebase.

### Test Statistics

- **Total Tests**: 100+ tests covering all major functionality including Excel file support
- **Test Framework**: pytest 7.0.0+
- **Coverage Tool**: pytest-cov 4.0.0+
- **Coverage Goal**: >80% overall, 100% for critical functions

### Key Features

- ✅ Fast execution (uses mocks to avoid slow I/O)
- ✅ Deterministic (no random behavior)
- ✅ Minimal dependencies (lazy imports + mocks)
- ✅ Clear error messages
- ✅ CI/CD ready

---

## Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── README.md                # Test documentation
│
└── unit/                    # Unit tests organized by package
    ├── config/              # Configuration tests
    │   ├── test_config_manager.py   # Config loading, merge, precedence
    │   └── test_config_schema.py    # Schema validation
    │
    ├── core/                # Core module tests
    │   ├── test_merge_processor.py  # Job execution, row processing
    │   ├── test_merge_orchestrator.py  # run_merge, run_merge_job
    │   ├── test_serial_number_parser.py  # Serial number parsing
    │   ├── test_csv_excel_reader.py  # CSV/Excel reading
    │   ├── test_result_reporter.py # Result formatting
    │   └── test_core_module_exports.py  # Module exports
    │
    ├── operations/          # Operations tests
    │   ├── test_pdf_merger.py       # PDF finding and merging
    │   ├── test_streaming_pdf_merger.py  # Streaming PDF operations
    │   └── test_excel_to_pdf_converter.py  # Excel to PDF conversion
    │
    ├── ui/                  # UI tests
    │   ├── test_app.py              # GUI application
    │   ├── test_components.py        # UI components
    │   ├── test_handlers.py         # Event handlers
    │   ├── test_license_ui.py      # License display
    │   └── test_ui_module_exports.py  # Module exports
    │
    ├── models/              # Domain model tests
    │   ├── test_row.py              # Row model
    │   ├── test_merge_job.py        # MergeJob model
    │   └── test_merge_result.py     # MergeResult model
    │
    ├── licensing/           # Licensing tests
    │   ├── test_license_manager.py   # License validation
    │   └── test_licensing_module_exports.py  # Module exports
    │
    ├── matching/            # Matching rules tests
    │   └── test_rules.py            # Formal matching rules
    │
    ├── observability/       # Observability tests
    │   ├── test_metrics.py          # Metrics collection
    │   ├── test_telemetry.py        # Telemetry
    │   └── test_crash_reporting.py  # Crash reporting
    │
    └── utils/               # Utility tests
        ├── test_validators.py       # Input validation
        ├── test_exceptions.py      # Exception classes
        ├── test_logging_utils.py   # Logging
        ├── test_path_utils.py      # Path handling
        └── test_utils_module_exports.py  # Module exports
```

### Test File Organization

Each test file follows a consistent structure:

```python
"""Tests for module_name."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_merger.module_name import function_to_test


class TestFunctionName:
    """Test cases for function_to_test."""
    
    def test_function_success(self):
        """Test successful execution."""
        result = function_to_test(valid_input)
        assert result == expected_output
    
    def test_function_error_handling(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            function_to_test(invalid_input)
```

---

## Running Tests

### Prerequisites

Ensure you have installed all dependencies:

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt
```

### Basic Test Execution

#### Run All Tests

```bash
pytest
```

#### Run with Verbose Output

```bash
pytest -v
```

#### Run Specific Test File

```bash
pytest tests/unit/utils/test_validators.py
```

#### Run Specific Test Class

```bash
pytest tests/unit/utils/test_validators.py::TestValidateSerialNumber
```

#### Run Specific Test Function

```bash
pytest tests/unit/utils/test_validators.py::TestValidateSerialNumber::test_valid_uppercase_serial_number
```

#### Run Tests Matching a Pattern

```bash
# Run all tests with "serial" in the name
pytest -k serial

# Run all tests in test_validators.py
pytest tests/unit/utils/test_validators.py
# Or by keyword
pytest -k validators
```

### Test Configuration

The project uses `pytest.ini` for configuration:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
```

This configuration:
- Automatically discovers tests in the `tests/` directory
- Runs with verbose output by default
- Shows short tracebacks on failures
- Enforces strict marker usage

---

## Test Coverage

### Generating Coverage Reports

#### Terminal Coverage Report

```bash
pytest --cov=pdf_merger --cov-report=term-missing
```

This shows:
- Overall coverage percentage
- Coverage per module
- Missing lines for each file

#### HTML Coverage Report

```bash
pytest --cov=pdf_merger --cov-report=html
```

This generates an HTML report in `htmlcov/index.html`. Open it in a browser:

```bash
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

#### Combined Report

```bash
pytest --cov=pdf_merger --cov-report=term-missing --cov-report=html
```

### Coverage Goals

- **Overall Coverage**: >80%
- **Critical Functions**: 100% (parsing, validation)
- **Utility Functions**: >70%

### Viewing Coverage

The HTML report provides:
- Line-by-line coverage highlighting
- Branch coverage information
- Missing line indicators
- Module-level summaries

---

## Test Categories

### 1. Unit Tests

Test individual functions and classes in isolation.

**Example:**
```python
def test_split_serial_numbers_single():
    """Test parsing a single serial number."""
    result = split_serial_numbers("GRNW_12345")
    assert result == ["GRNW_12345"]
```

**Characteristics:**
- Fast execution
- No external dependencies
- Tests one function at a time
- Uses fixtures for setup

### 2. Integration Tests

Test component interactions and workflows.

**Example:**
```python
def test_process_file_complete_workflow(tmp_path):
    """Test complete file processing workflow."""
    # Setup test files
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("serial_numbers\nGRNW_12345,GRNW_67890")
    
    pdf_folder = tmp_path / "pdfs"
    pdf_folder.mkdir()
    
    output_folder = tmp_path / "output"
    output_folder.mkdir()
    
    # Create test PDFs
    # ... setup code ...
    
    # Execute
    result = process_file(csv_file, pdf_folder, output_folder)
    
    # Verify
    assert result.successful_merges == 1
    assert result.total_rows == 1
```

**Characteristics:**
- Tests multiple components together
- Uses real file system (via `tmp_path` fixture)
- Verifies end-to-end workflows
- Can test PDF + Excel mixed merging scenarios

### 3. Mock Tests

Test with mocked external dependencies.

**Example:**
```python
@patch('pdf_merger.operations.pdf_merger._get_pdf_libraries')
def test_merge_pdfs_mocked(mock_get_libraries, tmp_path):
    """Test PDF merging with mocked PDF library."""
    # Setup mocks
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
    pdf_paths = [tmp_path / "test1.pdf", tmp_path / "test2.pdf"]
    output_path = tmp_path / "merged.pdf"
    
    result = merge_pdfs(pdf_paths, output_path)
    assert result is True
    mock_writer_instance.write.assert_called_once()
```

**Characteristics:**
- Mocks external libraries (PDF, file I/O)
- Fast execution
- No actual file operations
- Tests logic without dependencies

---

## Writing New Tests

### Test File Template

```python
"""Tests for module_name."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_merger.module_name import function_to_test


class TestFunctionName:
    """Test cases for function_to_test."""
    
    def test_function_success(self):
        """Test successful execution."""
        result = function_to_test(valid_input)
        assert result == expected_output
    
    def test_function_error_handling(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            function_to_test(invalid_input)
    
    def test_function_edge_case(self):
        """Test edge case handling."""
        result = function_to_test(edge_case_input)
        assert result is not None
```

### Best Practices

#### 1. Descriptive Test Names

Use clear, descriptive names that explain what is being tested:

```python
# Good
def test_split_serial_numbers_with_whitespace():
    """Test parsing serial numbers with whitespace."""
    pass

# Bad
def test_parse():
    """Test parsing."""
    pass
```

#### 2. One Assertion Per Test (When Possible)

```python
# Good - Clear what's being tested
def test_validate_serial_number_valid():
    """Test validation of valid serial number."""
    result = validate_serial_number("GRNW_12345")
    assert result is True

# Acceptable - Related assertions
def test_process_result_attributes():
    """Test ProcessingResult has all required attributes."""
    result = ProcessingResult(total_rows=5, successful_merges=4)
    assert result.total_rows == 5
    assert result.successful_merges == 4
    assert result.failed_rows == []
```

#### 3. Use Fixtures for Common Setup

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("serial_numbers\nGRNW_12345,GRNW_67890")
    return csv_file

def test_read_csv_file(sample_csv_file):
    """Test reading CSV file."""
    result = read_data_file(sample_csv_file)
    assert len(result) == 1
```

#### 4. Test Edge Cases

Always test:
- Empty inputs
- None values
- Invalid inputs
- Boundary conditions
- Error conditions

```python
def test_split_serial_numbers_empty_string():
    """Test parsing empty string."""
    result = split_serial_numbers("")
    assert result == []

def test_split_serial_numbers_none():
    """Test parsing None value."""
    with pytest.raises(ValueError):
        split_serial_numbers(None)
```

#### 5. Mock External Dependencies

```python
@patch('pdf_merger.file_reader.pd.read_csv')
def test_read_csv_mocked(mock_read_csv, tmp_path):
    """Test CSV reading with mocked pandas."""
    mock_read_csv.return_value = pd.DataFrame({'serial_numbers': ['GRNW_123']})
    result = read_data_file(tmp_path / "test.csv")
    assert len(result) == 1
```

### Test Organization

Organize tests into classes that group related test cases:

```python
class TestValidateSerialNumber:
    """Test cases for validate_serial_number function."""
    
    def test_valid_uppercase_serial_number(self):
        """Test validation of uppercase serial number."""
        pass
    
    def test_valid_lowercase_serial_number(self):
        """Test validation of lowercase serial number."""
        pass
    
    def test_invalid_no_prefix(self):
        """Test validation fails without GRNW_ prefix."""
        pass
```

---

## Troubleshooting

### Issue: Import errors when running tests

**Problem**: Tests can't import modules.

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/files_unifeder

# Verify virtual environment is activated
which python  # Should show .venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: PDF library errors

**Problem**: Tests fail with PDF library import errors.

**Solution:** PDF libraries use lazy imports. Most tests use mocks, but if you need real PDF testing:

```bash
pip install pypdf
```

**Note**: The lazy import system means:
- ✅ Module can be imported without pypdf
- ✅ Tests can run without pypdf (using mocks)
- ✅ Only fails if `merge_pdfs()` is called without pypdf installed AND without mocking

### Issue: Excel conversion library errors

**Problem**: Tests fail with Excel conversion import errors.

**Solution:** Excel conversion uses openpyxl and reportlab. Most tests use mocks, but if you need real Excel testing:

```bash
pip install openpyxl reportlab
```

**Note**: Excel conversion tests mock openpyxl and reportlab by default:
- ✅ Tests can run without openpyxl/reportlab (using mocks)
- ✅ Only fails if `convert_excel_to_pdf()` is called without libraries installed AND without mocking

### Issue: Tests fail with "file not found"

**Problem**: Tests try to access files that don't exist.

**Solution:** Use `tmp_path` fixture for temporary files:

```python
def test_with_file(tmp_path):
    """Test using temporary file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    # Use test_file in your test
    assert test_file.exists()
```

### Issue: Tests are slow

**Problem**: Tests take too long to run.

**Solution:**
1. Use mocks instead of real file I/O
2. Use `tmp_path` instead of creating files in actual directories
3. Avoid network calls (mock them)
4. Run specific tests during development: `pytest tests/unit/core/test_merge_processor.py`

### Issue: Coverage report shows 0%

**Problem**: Coverage isn't being measured correctly.

**Solution:**
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with explicit coverage
pytest --cov=pdf_merger --cov-report=term

# Check that source files are being found
pytest --cov=pdf_merger --cov-report=term --collect-only
```

### Issue: Tests pass locally but fail in CI

**Problem**: Environment differences.

**Solution:**
1. Check Python version matches
2. Ensure all dependencies are in `requirements.txt`
3. Verify test isolation (no shared state)
4. Check for platform-specific code (Windows vs Linux)

---

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

### CI Configuration Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest --cov=pdf_merger --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### CI Best Practices

- ✅ Run tests on multiple Python versions
- ✅ Run tests on multiple platforms (Linux, macOS, Windows)
- ✅ Generate coverage reports
- ✅ Fail build on test failures
- ✅ Cache dependencies for faster runs

---

## Additional Resources

- **Detailed Test Documentation**: See `tests/README.md`
- **Architecture Guide**: See `ARCHITECTURE.md` (in same directory)
- **Installation Guide**: See `INSTALLATION.md` (in same directory)
- **pytest Documentation**: https://docs.pytest.org/
- **Coverage.py Documentation**: https://coverage.readthedocs.io/

---

## Version

Current version: **1.0.0**
