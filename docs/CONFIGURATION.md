# Configuration Guide

This document describes how to configure PDF Batch Merger using various configuration methods.

## Configuration Precedence

Configuration values are resolved in the following order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **User Config File** (`~/.pdf_merger/config.json` or `config.json` in app directory)
3. **Per-Project Preset** (`.pdf_merger_config.json` in project directory)
4. **Defaults** (lowest priority)

Values from higher priority sources override values from lower priority sources.

## Environment Variables

Set these environment variables to configure the application:

- `PDF_MERGER_INPUT_FILE` - Path to the CSV or Excel input file
- `PDF_MERGER_SOURCE_DIR` - Path to the directory containing PDF and Excel source files
- `PDF_MERGER_OUTPUT_DIR` - Path to the output directory for merged PDFs
- `PDF_MERGER_COLUMN` - Name of the column containing serial numbers (default: `serial_numbers`)

### Example (Unix/Linux/macOS)

```bash
export PDF_MERGER_INPUT_FILE="/path/to/data.csv"
export PDF_MERGER_SOURCE_DIR="/path/to/source/files"
export PDF_MERGER_OUTPUT_DIR="/path/to/output"
export PDF_MERGER_COLUMN="serial_numbers"
```

### Example (Windows)

```cmd
set PDF_MERGER_INPUT_FILE=C:\path\to\data.csv
set PDF_MERGER_SOURCE_DIR=C:\path\to\source\files
set PDF_MERGER_OUTPUT_DIR=C:\path\to\output
set PDF_MERGER_COLUMN=serial_numbers
```

## User Config File

Create a configuration file at one of these locations:

- `~/.pdf_merger/config.json` (user home directory)
- `config.json` (in the application directory, for packaged apps)

### Config File Format

```json
{
  "input_file": "/path/to/data.csv",
  "pdf_dir": "/path/to/source/files",
  "output_dir": "/path/to/output",
  "required_column": "serial_numbers"
}
```

### Field Descriptions

- `input_file` - Path to the CSV or Excel input file
- `pdf_dir` - Path to the directory containing PDF and Excel source files (also accepts `source_dir` as an alias)
- `output_dir` - Path to the output directory for merged PDFs
- `required_column` - Name of the column containing serial numbers (default: `serial_numbers`)

## Per-Project Preset

Create a `.pdf_merger_config.json` file in your project directory to set project-specific defaults. The application will search for this file starting from the current working directory and walk up the directory tree.

### Example Project Preset

```json
{
  "pdf_dir": "./source_files",
  "output_dir": "./merged_output",
  "required_column": "serial_numbers"
}
```

This is useful when working on multiple projects with different source/output directories. The preset file is automatically discovered when running the application from within the project directory.

## Configuration Validation

All configuration values are validated:

- **Input file**: Must exist and be a file
- **Source directory**: Must exist and be a directory
- **Output directory**: Parent directory must exist (output directory will be created if needed)
- **Column name**: Must be a non-empty string

Invalid values are logged as warnings and the default value is used instead.

## Examples

### Example 1: Using Environment Variables

```bash
# Set environment variables
export PDF_MERGER_INPUT_FILE="/data/input.csv"
export PDF_MERGER_SOURCE_DIR="/data/source"
export PDF_MERGER_OUTPUT_DIR="/data/output"

# Launch the GUI application - it will use the environment variables
# to pre-populate the file selection fields
```

### Example 2: Using Per-Project Preset

```bash
# Create .pdf_merger_config.json in project root
cat > .pdf_merger_config.json << EOF
{
  "pdf_dir": "./pdfs",
  "output_dir": "./merged"
}
EOF

# Launch the GUI application from the project directory
# The preset will be automatically loaded and used to pre-populate fields
cd /path/to/project
# Then launch PDF Batch Merger
```

### Example 3: Full Configuration Stack

```bash
# 1. Per-project preset sets defaults
# .pdf_merger_config.json: { "pdf_dir": "./source" }

# 2. User config overrides preset
# ~/.pdf_merger/config.json: { "output_dir": "~/output" }

# 3. Environment variable overrides user config
export PDF_MERGER_INPUT_FILE="/data/input.csv"
export PDF_MERGER_OUTPUT_DIR="/tmp/output"
```

Final configuration (when GUI launches):
- `input_file`: `/data/input.csv` (from environment variable)
- `pdf_dir`: `./source` (from per-project preset)
- `output_dir`: `/tmp/output` (from environment variable, overrides user config)
- `required_column`: `serial_numbers` (default)

The GUI will pre-populate these values when launched.

## GUI Application

The GUI application automatically loads configuration on startup and pre-populates file selection fields when values are available from configuration sources (environment variables, config files, or per-project presets). Users can still modify these values through the file selection dialogs if needed.

## Troubleshooting

### Configuration Not Loading

1. Check that the config file exists at the expected location
2. Verify the JSON syntax is valid
3. Check application logs for validation warnings
4. Ensure file paths are absolute or relative to the working directory

### Path Issues

- Use absolute paths for reliability
- On Windows, use forward slashes or escaped backslashes in JSON: `"C:/path/to/file"` or `"C:\\path\\to\\file"`
- Paths are resolved to absolute paths during validation

### Environment Variables Not Working

1. Verify environment variables are set: `echo $PDF_MERGER_INPUT_FILE` (Unix) or `echo %PDF_MERGER_INPUT_FILE%` (Windows)
2. Ensure the application is reading from the same shell session where variables were set
3. Check that variable names match exactly (case-sensitive)
