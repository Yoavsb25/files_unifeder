# Configuration Guide

This document describes how to configure PDF Batch Merger using various configuration methods.

## Configuration Precedence

Configuration values are resolved in the following order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **CLI Arguments**
3. **User Config File** (`~/.pdf_merger/config.json` or `config.json` in app directory)
4. **Per-Project Preset** (`.pdf_merger_config.json` in project directory)
5. **Defaults** (lowest priority)

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

## CLI Arguments

Command-line arguments can override environment variables and config files:

```bash
python -m cli.command_line \
    --csv /path/to/data.csv \
    --folder /path/to/source/files \
    --output /path/to/output \
    --column serial_numbers
```

If environment variables are set, CLI arguments will override them.

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
export PDF_MERGER_SOURCE_DIR="/data/source"
export PDF_MERGER_OUTPUT_DIR="/data/output"

# Run with CLI arguments (env vars provide defaults)
python -m cli.command_line --csv /data/input.csv
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

# Run from project directory (preset is automatically loaded)
cd /path/to/project
python -m cli.command_line --csv data.csv
```

### Example 3: Full Configuration Stack

```bash
# 1. Per-project preset sets defaults
# .pdf_merger_config.json: { "pdf_dir": "./source" }

# 2. User config overrides preset
# ~/.pdf_merger/config.json: { "output_dir": "~/output" }

# 3. Environment variable overrides user config
export PDF_MERGER_OUTPUT_DIR="/tmp/output"

# 4. CLI argument overrides everything
python -m cli.command_line \
    --csv data.csv \
    --folder /custom/source \
    --output /custom/output
```

Final configuration:
- `input_file`: `data.csv` (from CLI)
- `pdf_dir`: `/custom/source` (from CLI, overrides preset)
- `output_dir`: `/custom/output` (from CLI, overrides env var and user config)
- `required_column`: `serial_numbers` (default)

## GUI Application

The GUI application currently uses manual file selection dialogs. Configuration files and environment variables can be used to set default values, but the GUI will still prompt for file selection if values are not provided.

Future versions may support loading configuration in the GUI to pre-populate file selection fields.

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
