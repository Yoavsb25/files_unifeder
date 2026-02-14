# Codebase improvement suggestions

This file collects suggestions for improving the codebase. They are non-blocking and can be addressed over time.

---

## Code Cleanup (Epic summary)

- **Removed / updated**: Stale references to `ProcessingResult`, `run_merge`, `process_file`, and `as_processing_result` have been removed from ARCHITECTURE.md, CODE_IMPROVEMENTS.md, and DEPRECATION.md. The pipeline uses only `MergeResult`.
- **Single source of truth**: Default column canonical value is `pdf_merger.models.defaults.DEFAULT_SERIAL_NUMBERS_COLUMN`; `core.csv_serial_constants` must stay in sync (test in `tests/unit/core/test_constants_sync.py`).
- **Legacy APIs kept (documented)**: `find_pdf_file` and `process_row` (bool-returning) are kept for backward compatibility and tests; prefer `find_source_file` and `process_row_with_models` + `MergeResult`.
- **Core enums**: `MatchConfidence` and `MatchBehavior` are no longer re-exported from `core.enums`; use `pdf_merger.models.enums` or `pdf_merger.matching` for matching.
- **Config**: All config load sites use `AppConfig.from_validated_dict()` so no raw dict builds config without validation.

---

## Exceptions

- **`PDFProcessingError`**  
  Used in production: raised by `operations.pdf_merger` and `operations.streaming_pdf_merger` on PDF read/merge/write failures. Callers (`row_pipeline`, `merge_processor`) catch it and map to row-level results.

---

## Result types and reporting

- **`ProcessingResult` and legacy API**  
  Removed per `DEPRECATION.md`. The pipeline uses only `MergeResult`; `process_job` returns `MergeResult`; `result_reporter` and `result_view` work with `MergeResult` / `ResultView`.

- **`format_result_detailed`**  
  The UI uses it in the "View detailed log" action (`_show_detailed_report`), which opens a dialog showing `format_result_detailed(result)` after a merge.

---

## Constants and duplication

- **Serial number and CSV constants (addressed)**  
  Serial number format constants now live only in `utils.serial_number_parser`; they were removed from `CsvSerialConstants`. CSV/encoding constants (`UTF_8_ENCODING`, `CSV_SAMPLE_SIZE`, `DEFAULT_CSV_DELIMITER`) now have a single source in `utils/csv_constants.py`; `column_reader` and `CsvSerialConstants` use or re-export from there.

- **Example column name in UI**  
  The UI placeholder “e.g. serial_numbers or Document ID” uses a literal string. If you want a single canonical example name, consider a constant (e.g. in `ui_constants` or `defaults`) and use it in both placeholder and helper text.

---

## Deprecations and removal

- **`run_merge`** and **`process_file`**  
  Removed as of 2.0 per `DEPRECATION.md`. Use `run_merge_job` or `load_job_from_file` + `process_job`.

---

## UI and structure

- **`pdf_merger/ui/app.py`**  
  The main app class is large. Consider extracting cohesive blocks into helpers or sub-modules (e.g. config loading, path application, validation state, run merge flow) to improve readability and testability.

- **Broad `except Exception`**  
  Several places catch `Exception` and log or show a generic message (e.g. `config_manager`, `handlers`, `row_pipeline`). Where possible, catch specific exceptions (`PDFMergerError`, `ValueError`, etc.) and re-raise or handle them explicitly so that unexpected errors are easier to diagnose.

---

## Tests and docs

- **`test_merge_processor.py`**  
  Comment at top references patching `utils.serial_number_parser` if merge_processor is refactored to import from utils; the processor already uses core’s re-export. You can update or remove that comment when touching this area.

- **ARCHITECTURE / IMPROVEMENT_ROADMAP**  
  If you remove or rename constants (e.g. `GOLDFARB_SERIAL_NUMBER_COLUMN`, `SOURCE_FILE_EXTENSIONS` from `FileConstants`), update any references in `docs/ARCHITECTURE.md` and `docs/IMPROVEMENT_ROADMAP.md`.

---

## Observability

- **Telemetry `endpoint`**  
  `TelemetryService.__init__` has an `endpoint` parameter “for future use”. Either implement sending events to that endpoint or document that it is reserved for a future backend.

- **MetricsCollector**  
  Metrics are recorded but not yet exported (e.g. to a file or external system). Consider adding a simple export hook (e.g. on shutdown or on demand) for debugging or future integration.
