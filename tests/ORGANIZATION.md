# Test Organization

## Structure

Tests are organized into logical categories under `tests/unit/`:

```
tests/
├── unit/
│   ├── data/           # Data processing tests
│   ├── operations/     # Operations tests
│   ├── core/           # Core module tests
│   ├── ui/             # UI tests
│   ├── licensing/      # Licensing tests
│   └── utils/          # Utility tests
```

## Categories

### `unit/data/`
Tests for data processing functionality:
- **test_data_parser.py** - Serial number parsing and normalization
- **test_file_reader.py** - CSV/Excel file reading
- **test_validators.py** - Input validation functions

### `unit/operations/`
Tests for file operations and processing:
- **test_pdf_operations.py** - PDF/Excel finding and merging
- **test_excel_converter.py** - Excel to PDF conversion
- **test_processor.py** - Main processing orchestration

### `unit/core/`
Tests for core business logic:
- **test_core.py** - Core merge orchestration and reporting
- **test_core_init.py** - Core module exports

### `unit/ui/`
Tests for user interface:
- **test_ui.py** - GUI application components
- **test_ui_init.py** - UI module exports

### `unit/licensing/`
Tests for license management:
- **test_licensing.py** - License validation and management
- **test_licensing_init.py** - Licensing module exports

### `unit/utils/`
Tests for utility modules:
- **test_logger.py** - Logging system
- **test_config.py** - Configuration management
- **test_exceptions.py** - Custom exception classes

## Benefits

1. **Better Organization**: Related tests are grouped together
2. **Easier Navigation**: Find tests by functionality category
3. **Selective Testing**: Run tests for specific areas
4. **Maintainability**: Clear structure makes it easier to maintain
5. **Scalability**: Easy to add new test categories as needed

## Running Tests

All tests can still be run from the root:

```bash
pytest                    # Run all tests
pytest tests/             # Run all tests (explicit)
```

Or by category:

```bash
pytest tests/unit/data/        # Data processing only
pytest tests/unit/operations/ # Operations only
```
