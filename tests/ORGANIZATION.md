# Test Organization

## Structure

Tests are organized into logical categories under `tests/unit/`:

```
tests/
├── unit/
│   ├── core/           # Core business logic tests
│   ├── operations/     # Operations tests
│   ├── ui/             # UI tests
│   ├── licensing/      # Licensing tests
│   ├── config/         # Configuration tests
│   ├── models/         # Data model tests
│   ├── matching/       # Matching rules tests
│   ├── observability/  # Observability tests
│   └── utils/          # Utility tests
```

## Categories

### `unit/core/`
Tests for core business logic:
- **test_merge_orchestrator.py** - Merge orchestration
- **test_result_reporter.py** - Result reporting
- **test_merge_processor.py** - Merge processing
- **test_csv_excel_reader.py** - CSV/Excel file reading
- **test_serial_number_parser.py** - Serial number parsing and normalization
- **test_core_module_exports.py** - Core module exports

### `unit/operations/`
Tests for file operations and processing:
- **test_pdf_merger.py** - PDF/Excel finding and merging
- **test_streaming_pdf_merger.py** - Streaming PDF merging
- **test_excel_to_pdf_converter.py** - Excel to PDF conversion

### `unit/ui/`
Tests for user interface:
- **test_app.py** - GUI application components
- **test_components.py** - UI components
- **test_handlers.py** - UI handlers
- **test_license_ui.py** - License UI
- **test_ui_module_exports.py** - UI module exports

### `unit/licensing/`
Tests for license management:
- **test_license_manager.py** - License validation and management
- **test_licensing_module_exports.py** - Licensing module exports

### `unit/config/`
Tests for configuration management:
- **test_config_manager.py** - Configuration management
- **test_config_schema.py** - Configuration schema

### `unit/models/`
Tests for data models:
- **test_merge_job.py** - Merge job model
- **test_merge_result.py** - Merge result model
- **test_row.py** - Row model

### `unit/matching/`
Tests for matching rules:
- **test_rules.py** - Matching rules

### `unit/observability/`
Tests for observability:
- **test_crash_reporting.py** - Crash reporting
- **test_metrics.py** - Metrics
- **test_telemetry.py** - Telemetry

### `unit/utils/`
Tests for utility modules:
- **test_exceptions.py** - Custom exception classes
- **test_logging_utils.py** - Logging system
- **test_path_utils.py** - Path utilities
- **test_validators.py** - Input validation functions
- **test_utils_module_exports.py** - Utils module exports

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
pytest tests/unit/core/        # Core logic only
pytest tests/unit/operations/ # Operations only
pytest tests/unit/ui/         # UI only
pytest tests/unit/utils/      # Utilities only
```
