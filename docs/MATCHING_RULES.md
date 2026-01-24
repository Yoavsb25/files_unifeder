# Matching Rules Documentation

## Overview

PDF Batch Merger uses a formal matching algorithm to find source files (PDF and Excel) based on serial numbers from your input data. This document explains how the matching works and how to handle common scenarios.

## How Matching Works

The application searches for files in the source directory that match each serial number. The matching follows a strict priority order:

### 1. Exact Match (Highest Priority)

The system first looks for files with an exact filename match (case-insensitive):

- **Serial Number**: `GRNW_12345`
- **Matches**: `GRNW_12345.pdf`, `grnw_12345.xlsx`, `GRNW_12345.PDF`

### 2. Stem Match (Fallback)

If no exact match is found, the system looks for files where the stem (filename without extension) matches:

- **Serial Number**: `GRNW_12345`
- **Matches**: `GRNW_12345_v2.pdf`, `GRNW_12345_final.xlsx`

The stem is the filename without the extension, so `GRNW_12345_v2.pdf` has stem `GRNW_12345_v2`.

### 3. Deterministic Selection

When multiple files match, the system selects the first file alphabetically (by full path). This ensures consistent behavior across runs.

## Case Sensitivity

Matching is **case-insensitive** on all platforms:

- `GRNW_12345` matches `grnw_12345.pdf`
- `TestFile` matches `testfile.xlsx`

## Unicode and Special Characters

The system handles Unicode characters correctly across platforms:

- Files with accented characters (é, ñ, ü, etc.) are matched correctly
- Works correctly on macOS (which uses decomposed Unicode) and Windows/Linux
- Special characters in filenames are handled properly

## Ambiguous Matches

When multiple files match the same serial number, this is called an "ambiguous match." The system can handle this in different ways:

### Production Mode (Default)

In production mode, ambiguous matches cause an error:

```
Error: Ambiguous match for 'GRNW_12345': multiple files found:
  - /path/to/GRNW_12345.pdf
  - /path/to/GRNW_12345.xlsx
```

**Action**: You must resolve the ambiguity by:
1. Renaming one of the files
2. Removing duplicate files
3. Using more specific serial numbers

### Development Mode

In development mode, the system logs a warning and uses the first match (alphabetically):

```
Warning: Ambiguous match for 'GRNW_12345': multiple files found. Using first match: GRNW_12345.pdf
```

## Common Scenarios

### Scenario 1: Single Exact Match

**Input**: Serial number `GRNW_12345`  
**Files**: `GRNW_12345.pdf`  
**Result**: ✅ Matches `GRNW_12345.pdf`

### Scenario 2: Multiple File Types

**Input**: Serial number `GRNW_12345`  
**Files**: `GRNW_12345.pdf`, `GRNW_12345.xlsx`  
**Result**: ⚠️ Ambiguous match (error in production mode)

**Solution**: Rename one file or use more specific serial numbers.

### Scenario 3: Versioned Files

**Input**: Serial number `GRNW_12345`  
**Files**: `GRNW_12345_v1.pdf`, `GRNW_12345_v2.pdf`  
**Result**: ⚠️ Ambiguous match (both match by stem)

**Solution**: Use more specific serial numbers like `GRNW_12345_v1` and `GRNW_12345_v2`.

### Scenario 4: Case Variations

**Input**: Serial number `grnw_12345`  
**Files**: `GRNW_12345.pdf`  
**Result**: ✅ Matches `GRNW_12345.pdf` (case-insensitive)

### Scenario 5: File Not Found

**Input**: Serial number `GRNW_99999`  
**Files**: (no matching file)  
**Result**: ⚠️ No match found, row is skipped

## Best Practices

### 1. Use Consistent Naming

- Use consistent serial number formats
- Avoid version suffixes in filenames if possible
- Use unique identifiers for each file

### 2. Avoid Ambiguity

- Don't have multiple files with the same base name
- Use descriptive filenames when versions are needed
- Consider using subdirectories for different file types

### 3. Handle Special Characters

- Unicode characters are supported but should be used consistently
- Test matching if you use special characters in filenames

### 4. Organize Files

- Keep source files well-organized
- Use clear, descriptive filenames
- Avoid duplicate files with similar names

## Troubleshooting

### "Ambiguous match" Error

**Problem**: Multiple files match the same serial number.

**Solutions**:
1. Check your source directory for duplicate filenames
2. Rename files to be more specific
3. Use more detailed serial numbers in your input data
4. Remove unnecessary duplicate files

### "File not found" Warning

**Problem**: No file matches a serial number.

**Solutions**:
1. Check that the serial number in your input data matches the filename
2. Verify the file exists in the source directory
3. Check for typos in serial numbers
4. Ensure the file has a supported extension (.pdf, .xlsx, .xls)

### Case Sensitivity Issues

**Problem**: Files not matching due to case differences.

**Note**: Matching is case-insensitive, so this shouldn't be an issue. If you're experiencing problems:
1. Check for hidden characters or Unicode issues
2. Verify the file extension is correct
3. Try renaming the file to match exactly

## Technical Details

For detailed technical specifications, see `pdf_merger/matching/spec.md` in the source code.

Key technical points:
- Matching uses Unicode NFC normalization
- Files are sorted alphabetically by full path for deterministic selection
- Performance is optimized for directories with many files
- The algorithm is O(n) where n is the number of files in the directory
