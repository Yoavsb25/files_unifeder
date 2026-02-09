# Coding Style Guide

This document defines coding style for the PDF Merger codebase so new code stays consistent.

## Quote style

- **Use double quotes (`"`) for strings** in Python source.
- Use single quotes only when the string contains double quotes and escaping would be noisy.

Example:

```python
message = "Processing complete"
error = "File not found"
```

## Docstrings

- **Use the Google style** for all public API docstrings (modules, classes, and functions that are part of the public API or important for maintainability).
- Include **Args**, **Returns**, and **Raises** (when applicable) with types and one-line descriptions.

Example:

```python
def run_merge_job(
    input_file: Path,
    pdf_dir: Path,
    output_dir: Path,
    required_column: str = "serial_numbers",
    job_id: Optional[str] = None,
    fail_on_ambiguous: bool = True,
) -> MergeResult:
    """Run the merge operation using domain models.

    Args:
        input_file: Path to CSV or Excel file.
        pdf_dir: Path to folder containing PDF and Excel files.
        output_dir: Path to output folder.
        required_column: Name of the column containing serial numbers.
        job_id: Optional job identifier for tracking.
        fail_on_ambiguous: If True, raise on ambiguous file matches.

    Returns:
        MergeResult with detailed processing results.
    """
```

For private helpers, a single-line docstring is acceptable.

## Trailing commas

- **Use trailing commas in multi-line lists, dicts, tuples, and argument lists.** This keeps diffs minimal when adding or reordering items.

Example:

```python
__all__ = [
    "process_file",
    "merge_pdfs",
    "ValidationError",
]

return AppConfig(
    input_file=value,
    required_column=column,
)  # trailing comma here
```

## Boolean return values at call sites

- When storing the result of a function that returns `bool` (e.g. `convert_excel_to_pdf`, `merge_pdfs`), use a name that conveys intent: **`success`**, **`ok`**, or **`found`** as appropriate.

Example:

```python
success = convert_excel_to_pdf(excel_path, output_path)
if success:
    pdf_paths.append(output_path)

ok = merge_pdfs(pdf_paths, output_path)
if not ok:
    return RowResult(...)
```

## One statement per line

- Avoid packing multiple logical statements on one line. Prefer a local variable or helper when an expression is long (e.g. in function calls or conditionals) so the code stays scannable.
