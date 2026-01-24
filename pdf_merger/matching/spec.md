# Matching Rules Specification

## Overview

This document specifies the formal matching algorithm used to find source files (PDF and Excel) based on serial numbers from the input data.

## Matching Algorithm

The matching algorithm follows a strict priority order with deterministic tie-breaking:

### Priority Order

1. **Exact Match** (highest priority)
   - Case-insensitive filename match
   - Matches filename with or without extension
   - Example: `GRNW_12345` matches `grnw_12345.pdf`, `GRNW_12345.xlsx`, `grnw_12345.PDF`

2. **Stem Match** (fallback)
   - Case-insensitive match on filename without extension
   - Example: `GRNW_12345` matches `GRNW_12345_v2.pdf` (stem: `GRNW_12345_v2`)

3. **Deterministic Tie-Breaking** (when multiple matches exist)
   - Files are sorted alphabetically by full resolved path
   - First match in sorted order is selected
   - Ensures consistent behavior across runs

## Unicode Normalization

For cross-platform compatibility, all filenames are normalized using Unicode NFC (Normalization Form Composed):

- **macOS**: Uses NFD (decomposed) by default, normalized to NFC for matching
- **Windows**: Uses NFC by default
- **Linux**: Uses NFC by default

This ensures that files with accented characters or special Unicode characters match correctly across platforms.

## Ambiguity Detection

When multiple files match a serial number, the system detects this as an ambiguous match.

### Ambiguity Handling Modes

1. **FAIL_FAST** (default for production)
   - Raises `ValueError` when ambiguous matches are detected
   - Prevents silent wrong merges
   - Requires explicit resolution

2. **WARN_FIRST** (development mode)
   - Logs warning with all matches
   - Uses first match (alphabetically sorted)
   - Continues processing

3. **LOG_ALL** (debugging mode)
   - Logs all matches with details
   - Uses first match (alphabetically sorted)
   - Provides full visibility for debugging

## Performance Considerations

### Large Directories

For directories with many files (>1000 files), the matching algorithm:

1. **Iterates through files once** - O(n) complexity
2. **Uses case-insensitive comparison** - Fast string operations
3. **Sorts matches only when needed** - Lazy sorting
4. **Caches directory listings** - Can be optimized with indexing (future enhancement)

### Optimization Strategies

- **Indexing**: Build an index of filenames for O(1) lookup (for very large directories)
- **Caching**: Cache directory listings to avoid repeated filesystem access
- **Parallel search**: For multiple serial numbers, can search in parallel

## Examples

### Example 1: Exact Match

```
Serial Number: GRNW_12345
Files in folder:
  - GRNW_12345.pdf
  - GRNW_12346.pdf

Result: Matches GRNW_12345.pdf (exact match, confidence: EXACT)
```

### Example 2: Stem Match

```
Serial Number: GRNW_12345
Files in folder:
  - GRNW_12345_v2.pdf
  - GRNW_12345_final.xlsx

Result: Matches GRNW_12345_v2.pdf (stem match, first alphabetically, confidence: STEM)
```

### Example 3: Ambiguous Match

```
Serial Number: GRNW_12345
Files in folder:
  - GRNW_12345.pdf
  - GRNW_12345.xlsx
  - GRNW_12345_final.pdf

Behavior: FAIL_FAST
Result: ValueError("Ambiguous match for 'GRNW_12345': multiple files found...")

Behavior: WARN_FIRST
Result: Warning logged, uses GRNW_12345.pdf (first alphabetically)
```

### Example 4: Unicode Normalization

```
Serial Number: café
Files in folder (macOS NFD):
  - café.pdf (decomposed: c + a + f + e + ́)

Normalization: Both normalized to NFC (café)
Result: Matches café.pdf (exact match after normalization)
```

## Implementation Details

### Case Sensitivity

- Matching is **case-insensitive** on all platforms
- Windows filesystems are case-insensitive by default
- macOS and Linux filesystems are case-sensitive, but matching normalizes to lowercase

### Path Resolution

- All paths are resolved to absolute paths before comparison
- Ensures consistent matching regardless of working directory
- Handles symbolic links correctly

### Extension Handling

- Supported extensions: `.pdf`, `.xlsx`, `.xls`
- Extension matching is case-insensitive
- Files without extensions are not matched (by design)

## Error Handling

- **File not found**: Returns `None` (no match)
- **Permission denied**: Logs warning, returns `None`
- **Ambiguous match (FAIL_FAST)**: Raises `ValueError`
- **Invalid folder**: Returns empty match list

## Testing

The matching algorithm is tested for:

- Exact matches (various cases)
- Stem matches
- Ambiguous matches (all behaviors)
- Unicode normalization (NFD/NFC)
- Case insensitivity
- Large directory performance
- Cross-platform compatibility
