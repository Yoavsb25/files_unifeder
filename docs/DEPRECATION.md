# Deprecation notice

This document lists deprecated APIs and their planned removal.

## Timeline

- **Version 2.0**: Removal of deprecated entry points and legacy result type from the public API. Internal use may still be supported for one release cycle if needed.

## Deprecated APIs

### Merge entry points

| Symbol | Replacement | Notes |
|--------|-------------|--------|
| `run_merge` | `run_merge_job` | Same behavior; `run_merge_job` returns `MergeResult` and is the single preferred entry point. For legacy `ProcessingResult`, use `as_processing_result(merge_result)` from `pdf_merger.core.result_types`. |
| `process_file` | `load_job_from_file` + `process_job` | Build a `MergeJob` with `load_job_from_file(...)`, then call `process_job(job, ...)`. Use `as_processing_result(merge_result)` if you need `ProcessingResult`. |

### Result type

| Symbol | Replacement | Notes |
|--------|-------------|--------|
| `ProcessingResult` | `MergeResult` | `MergeResult` has per-row details and timing. Use `as_processing_result(merge_result)` when calling legacy code that expects `ProcessingResult`. |

## Migration example

**Before (deprecated):**

```python
from pdf_merger import run_merge

result = run_merge(input_file, pdf_dir, output_dir, required_column="serial_numbers")
# result is MergeResult
```

**After (preferred):**

```python
from pdf_merger import run_merge_job

result = run_merge_job(
    input_file=input_file,
    pdf_dir=pdf_dir,
    output_dir=output_dir,
    required_column="serial_numbers",
)
# result is MergeResult; same as before, no adapter needed
```

**If you need ProcessingResult for legacy callers:**

```python
from pdf_merger import run_merge_job
from pdf_merger.core.result_types import as_processing_result

merge_result = run_merge_job(...)
legacy_result = as_processing_result(merge_result)
```

**Replacing process_file:**

```python
from pdf_merger.core.job_loader import load_job_from_file
from pdf_merger.core.merge_processor import process_job
from pdf_merger.core.result_types import as_processing_result

job = load_job_from_file(file_path, source_folder, output_folder, required_column, on_progress=...)
merge_result = process_job(job, on_progress=...)
legacy_result = as_processing_result(merge_result)
```
