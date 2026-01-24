# PDF Batch Merger

A desktop application for merging PDF and Excel files into PDF documents based on instructions from CSV or Excel files. Designed for law firms and businesses that need to combine documents and spreadsheets in bulk.

## Features

- **PDF Merging**: Merge multiple PDF files into a single document
- **Excel Support**: Convert Excel files (.xlsx, .xls) to PDF and merge with PDFs
- **Mixed Merging**: Combine PDF and Excel files in any combination
- **Batch Processing**: Process multiple merge operations from a single CSV/Excel file
- **Case-Insensitive Matching**: Automatically finds files regardless of case
- **Modern GUI**: Built with CustomTkinter for a clean, cross-platform interface
- **License Management**: RSA-signed license validation system

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Prepare Your Files**:
   - Create a CSV or Excel file with a `serial_numbers` column
   - Place PDF and Excel files in a source folder
   - Select files and folders in the GUI
   - Click "Run Merge"

## Requirements

- Python 3.6 or higher
- See `requirements.txt` for full dependency list:
  - `pypdf>=3.0.0` - PDF merging
  - `openpyxl>=3.0.0` - Excel file reading
  - `reportlab>=3.6.0` - Excel to PDF conversion
  - `pandas>=1.3.0` - Data manipulation
  - `customtkinter>=5.0.0` - GUI framework
  - `cryptography>=41.0.0` - License signing

## Documentation

- **[User Guide](docs/README_USER.md)** - How to use the application
- **[Installation Guide](INSTALLATION.md)** - Detailed installation instructions
- **[Architecture Documentation](ARCHITECTURE.md)** - System architecture and design
- **[Testing Guide](TESTING.md)** - Running and writing tests

## Recent Changes

### Version 1.0.0 - Excel File Support

- ✅ Added support for merging Excel files (.xlsx, .xls) with PDFs
- ✅ Excel files are automatically converted to PDF before merging
- ✅ Support for mixed merges (PDF + Excel, Excel + Excel, PDF + PDF)
- ✅ Updated UI to reflect "Source Directory" instead of "PDF Directory"
- ✅ Improved error handling and logging
- ✅ Suppressed noisy PDF read warnings for Apple-annotated PDFs

## Usage Example

1. Create an input file (`input.xlsx`) with a `serial_numbers` column:
   ```
   serial_numbers
   GRNW_1, GRNW_2
   GRNW_3.xlsx, GRNW_4.pdf
   ```

2. Place source files in a folder:
   - `GRNW_1.pdf`
   - `GRNW_2.pdf`
   - `GRNW_3.xlsx`
   - `GRNW_4.pdf`

3. Run the application and select:
   - Input file: `input.xlsx`
   - Source directory: folder containing the files
   - Output directory: where merged PDFs will be saved

4. Results:
   - `merged_row_1.pdf` - Contains GRNW_1.pdf + GRNW_2.pdf
   - `merged_row_2.pdf` - Contains GRNW_3.xlsx (converted to PDF) + GRNW_4.pdf

## Project Structure

```
files_unifeder/
├── pdf_merger/          # Main application package
│   ├── core/            # Core business logic
│   ├── ui/              # GUI application
│   ├── licensing/       # License management
│   ├── excel_converter.py  # Excel to PDF conversion
│   ├── pdf_operations.py   # PDF finding and merging
│   └── processor.py     # Main processing logic
├── tests/               # Test suite
├── docs/                # Documentation
├── tools/               # Development tools
└── requirements.txt     # Python dependencies
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf_merger --cov-report=html
```

### Building

See `INSTALLATION.md` for build instructions using PyInstaller.

## License

This software uses a license management system. Contact the software provider for license information.

## Support

For technical support or license issues, please contact your software provider.

---

**Version**: 1.0.0
