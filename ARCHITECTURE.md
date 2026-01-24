# PDF Batch Merger - Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Structure](#component-structure)
4. [Data Flow](#data-flow)
5. [Architecture Principles](#architecture-principles)

---

## Overview

PDF Batch Merger is a desktop application built with Python that merges multiple PDF and Excel files into PDF documents based on instructions from CSV or Excel files. The application follows a modular architecture with clear separation of concerns between business logic, user interface, and data processing.

### Key Features

- **GUI Application**: Built with CustomTkinter for a modern, cross-platform interface
- **License Management**: RSA-signed license validation system
- **Modular Design**: Clean separation between core logic, UI, and utilities
- **Comprehensive Testing**: Full test coverage with pytest
- **Multiple Input Formats**: Supports CSV and Excel files
- **Mixed File Support**: Can merge PDF and Excel files together (Excel files are converted to PDF)
- **Flexible File Matching**: Case-insensitive filename matching for PDF and Excel files

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        GUI[GUI Application<br/>CustomTkinter]
        CLI[CLI Interface<br/>Optional]
    end
    
    subgraph "Application Layer"
        Main[main.py<br/>Entry Point]
        License[License Manager<br/>Validation]
    end
    
    subgraph "Business Logic Layer"
        Core[Core Module<br/>Business Logic]
        Processor[Processor<br/>Orchestration]
        Validator[Validators<br/>Input Validation]
    end
    
    subgraph "Data Processing Layer"
        FileReader[File Reader<br/>CSV/Excel]
        DataParser[Data Parser<br/>Serial Numbers]
        PDFOps[PDF Operations<br/>Find & Merge]
        ExcelConv[Excel Converter<br/>Excel to PDF]
    end
    
    subgraph "Infrastructure Layer"
        Logger[Logger<br/>Logging System]
        Exceptions[Custom Exceptions<br/>Error Handling]
    end
    
    GUI --> Main
    CLI --> Main
    Main --> License
    License --> Core
    Core --> Processor
    Processor --> Validator
    Processor --> FileReader
    Processor --> DataParser
    Processor --> PDFOps
    Processor --> ExcelConv
    Processor --> Logger
    ExcelConv --> PDFOps
    Validator --> Exceptions
    FileReader --> Exceptions
    PDFOps --> Exceptions
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant GUI
    participant Main
    participant License
    participant Core
    participant Processor
    participant Validator
    participant FileReader
    participant PDFOps
    participant ExcelConv
    
    User->>GUI: Launch Application
    GUI->>Main: Start Application
    Main->>License: Check License Status
    License-->>Main: License Status
    
    alt License Valid
        Main->>GUI: Launch GUI
        User->>GUI: Select Files & Run Merge
        GUI->>Core: run_merge()
        Core->>Validator: Validate Inputs
        Validator-->>Core: Validation Result
        Core->>Processor: process_file()
        Processor->>FileReader: read_data_file()
        FileReader-->>Processor: DataFrame
        loop For Each Row
        Processor->>PDFOps: find_source_file()
        PDFOps-->>Processor: File Paths (PDF/Excel)
        alt Excel File Found
            Processor->>ExcelConv: convert_excel_to_pdf()
            ExcelConv->>ExcelConv: Read Excel (openpyxl)
            ExcelConv->>ExcelConv: Generate PDF (reportlab)
            ExcelConv-->>Processor: Temporary PDF Path
        end
        Processor->>PDFOps: merge_pdfs()
        PDFOps-->>Processor: Merged PDF
        Processor->>Processor: Cleanup Temp Files
        end
        Processor-->>Core: ProcessingResult
        Core-->>GUI: Result Summary
        GUI-->>User: Display Results
    else License Invalid
        Main->>GUI: Show Error & Exit
    end
```

---

## Component Structure

### Directory Structure

```
files_unifeder/
├── main.py                      # Application entry point
├── pdf_merger/                   # Main package
│   ├── __init__.py              # Public API exports
│   ├── config.py                # Configuration settings with precedence
│   ├── config_schema.py         # Configuration schema and validation
│   ├── logger.py                # Logging configuration
│   ├── exceptions.py            # Custom exception classes
│   │
│   ├── core/                    # Business logic layer
│   │   ├── merger.py           # Core merge orchestration
│   │   └── reporter.py         # Result formatting
│   │
│   ├── processor.py            # Main processing orchestration
│   ├── validators.py            # Input validation functions
│   ├── data_parser.py           # Serial number parsing
│   ├── file_reader.py           # CSV/Excel file reading
│   ├── pdf_operations.py        # PDF finding and merging
│   ├── excel_converter.py       # Excel to PDF conversion
│   │
│   ├── ui/                      # User interface
│   │   ├── app.py              # CustomTkinter GUI application
│   │   └── __init__.py
│   │
│   └── licensing/               # License management
│       ├── license_manager.py  # License validation
│       ├── license_model.py    # License data model
│       └── license_signer.py   # RSA signing/verification
│
├── cli/                         # Command-line interfaces (optional)
│   ├── command_line.py         # CLI with arguments
│   └── interactive.py          # Interactive prompts
│
├── tests/                       # Test suite
│   ├── test_*.py               # Unit tests for each module
│   └── README.md               # Testing documentation
│
├── tools/                       # Development tools
│   └── license_generator.py    # License generation tool
│
└── requirements.txt            # Python dependencies
```

### Core Components

#### 1. Entry Point (`main.py`)

- **Responsibility**: Application bootstrap and license checking
- **Flow**: 
  1. Initialize logging
  2. Check license status
  3. Launch GUI if license valid
  4. Handle license errors gracefully

```mermaid
flowchart TD
    Start([Application Start]) --> Init[Initialize Logging]
    Init --> CheckLicense[Check License Status]
    CheckLicense --> Valid{License Valid?}
    Valid -->|Yes| LaunchGUI[Launch GUI]
    Valid -->|Expired| ShowWarning[Show Warning<br/>Launch GUI with Restrictions]
    Valid -->|Invalid| ShowError[Show Error<br/>Exit Application]
    LaunchGUI --> End([Application Running])
    ShowWarning --> End
    ShowError --> Exit([Exit])
```

#### 2. Core Module (`pdf_merger/core/`)

- **`merger.py`**: High-level merge orchestration
  - Coordinates validation, processing, and result formatting
  - Decouples UI from business logic
  
- **`reporter.py`**: Result formatting
  - Formats processing results for display
  - Generates summary and detailed reports

#### 3. Processor (`pdf_merger/processor.py`)

- **Responsibility**: Main processing orchestration
- **Key Functions**:
  - `process_file()`: Process entire CSV/Excel file
  - `process_row()`: Process single row (handles PDF and Excel files)
  - Returns `ProcessingResult` with statistics
- **Excel Handling**:
  - Finds both PDF and Excel files using `find_source_file()`
  - Converts Excel files to temporary PDFs using `convert_excel_to_pdf()`
  - Merges all PDFs (original + converted Excel PDFs)
  - Automatically cleans up temporary PDF files after merging
  - Handles conversion errors gracefully (logs and continues with other files)

#### 4. Validators (`pdf_merger/validators.py`)

- **Responsibility**: Input validation
- **Validates**:
  - File existence and format
  - Folder existence
  - Required columns in data files
  - Serial number format (GRNW_ prefix)
  - Complete path sets

#### 5. File Reader (`pdf_merger/file_reader.py`)

- **Responsibility**: Reading CSV and Excel files
- **Features**:
  - Auto-detects file type (.csv, .xlsx, .xls)
  - Auto-detects CSV delimiter (comma, semicolon, tab)
  - Unified interface for all file types
  - Returns pandas DataFrame

#### 6. Data Parser (`pdf_merger/data_parser.py`)

- **Responsibility**: Parsing serial numbers from strings
- **Features**:
  - Handles comma-separated values
  - Strips whitespace
  - Validates format

#### 7. PDF Operations (`pdf_merger/pdf_operations.py`)

- **Responsibility**: PDF file operations
- **Features**:
  - `find_source_file()`: Case-insensitive finding of PDF and Excel files
  - `find_pdf_file()`: Case-insensitive PDF finding (backward compatibility)
  - `merge_pdfs()`: Merging multiple PDFs into one
  - Lazy loading of PDF libraries (pypdf)
  - Suppresses noisy PDF read warnings (Apple-annotated PDFs)
- **Implementation Details**:
  - Uses `strict=False` mode for pypdf to handle problematic PDFs
  - Suppresses stderr during PDF reading to avoid noisy warnings
  - Handles PdfReadError exceptions gracefully
  - Supports both pypdf and PyPDF2 libraries (with pypdf preferred)

#### 7a. Excel Converter (`pdf_merger/excel_converter.py`)

- **Responsibility**: Converting Excel files to PDF format
- **Features**:
  - `convert_excel_to_pdf()`: Converts .xlsx and .xls files to PDF
  - Uses openpyxl to read Excel files and reportlab to generate PDFs
  - Handles empty cells and None values gracefully
  - Creates formatted PDF tables from Excel data
  - Supports both .xlsx and .xls formats (note: openpyxl primarily supports .xlsx)
- **Dependencies**:
  - `openpyxl>=3.0.0` - Excel file reading
  - `reportlab>=3.6.0` - PDF generation
- **Implementation Details**:
  - Reads all rows from the active Excel sheet
  - Converts data to a formatted PDF table with headers
  - Handles styling (headers, borders, colors)
  - Preserves data structure in PDF format

#### 8. UI Module (`pdf_merger/ui/app.py`)

- **Responsibility**: GUI application
- **Technology**: CustomTkinter
- **Features**:
  - File/folder selection dialogs
  - Real-time progress logging
  - Result display
  - License status indicator
  - Updated labels: "Source Directory" (supports PDF and Excel files)
- **UI Updates**:
  - Changed "PDF Directory" to "Source Directory" to reflect Excel support
  - Updated dialog titles and validation messages
  - Shows Excel conversion progress in logs

#### 9. Licensing System (`pdf_merger/licensing/`)

- **`license_manager.py`**: License validation and status checking
- **`license_model.py`**: License data structure
- **`license_signer.py`**: RSA signature generation and verification

```mermaid
graph LR
    subgraph "License Generation"
        PrivateKey[Private Key<br/>tools/private_key.pem]
        Generator[License Generator<br/>tools/license_generator.py]
        LicenseFile[License File<br/>license.json]
    end
    
    subgraph "Application"
        PublicKey[Public Key<br/>Embedded in App]
        LicenseMgr[License Manager]
        Validation[Signature Verification]
    end
    
    PrivateKey --> Generator
    Generator --> LicenseFile
    PublicKey --> LicenseMgr
    LicenseFile --> LicenseMgr
    LicenseMgr --> Validation
    Validation --> Status[License Status]
```

---

## Data Flow

### Processing Flow

```mermaid
flowchart TD
    Start([User Clicks Run Merge]) --> Validate[Validate Inputs]
    Validate -->|Invalid| Error[Show Error]
    Validate -->|Valid| ReadFile[Read CSV/Excel File]
    ReadFile --> ParseRows[Parse Rows]
    ParseRows --> Loop{For Each Row}
    Loop --> ParseSerials[Parse Serial Numbers]
    ParseSerials --> FindFiles[Find Source Files<br/>PDF & Excel]
    FindFiles --> ConvertExcel{Excel Files?}
    ConvertExcel -->|Yes| Convert[Convert Excel to PDF<br/>Create Temp PDF]
    ConvertExcel -->|No| CheckFound{Files Found?}
    Convert --> CheckFound
    CheckFound -->|No| Warn[Log Warning<br/>Skip Row]
    CheckFound -->|Yes| Merge[Merge PDFs<br/>Original + Converted]
    Warn --> NextRow
    Merge --> Save[Save Merged PDF]
    Save --> Cleanup[Cleanup Temp Files]
    Cleanup --> NextRow{More Rows?}
    NextRow -->|Yes| Loop
    NextRow -->|No| Summary[Generate Summary]
    Summary --> Display[Display Results]
    Error --> End([End])
    Display --> End
```

### File Processing Pipeline

```mermaid
graph TB
    subgraph "Input"
        CSV[CSV/Excel File<br/>serial_numbers column]
        SourceFiles[Source Files Folder<br/>PDF & Excel]
    end
    
    subgraph "Processing"
        Read[File Reader<br/>Detect Type & Read]
        Parse[Data Parser<br/>Parse Serial Numbers]
        Find[PDF Operations<br/>Find Source Files]
        Convert[Excel Converter<br/>Convert Excel to PDF]
        Merge[PDF Operations<br/>Merge PDFs]
    end
    
    subgraph "Output"
        Merged[Merged PDFs<br/>merged_row_N.pdf]
        Log[Processing Log<br/>Summary & Errors]
    end
    
    CSV --> Read
    Read --> Parse
    Parse --> Find
    SourceFiles --> Find
    Find --> Convert
    Convert --> Merge
    Find --> Merge
    Merge --> Cleanup[Cleanup Temp PDFs]
    Cleanup --> Merged
    Merge --> Log
```

---

## Architecture Principles

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data processing
2. **Modularity**: Each module has a single, well-defined responsibility
3. **Testability**: Components are designed to be easily testable with mocks
4. **Extensibility**: New features can be added without modifying core logic (Excel support added without breaking existing PDF-only workflows)
5. **Error Handling**: Comprehensive exception hierarchy for clear error messages
6. **Logging**: Structured logging throughout for debugging and monitoring
7. **Backward Compatibility**: Existing functionality preserved when adding new features
8. **Resource Management**: Automatic cleanup of temporary files (Excel-to-PDF conversions)

---

## Technical Details

### Excel to PDF Conversion

The Excel converter uses a two-step process:

1. **Reading**: Uses `openpyxl` to read Excel files (.xlsx format)
   - Reads all rows from the active sheet
   - Handles empty cells (converts None to empty strings)
   - Preserves data structure

2. **PDF Generation**: Uses `reportlab` to create formatted PDFs
   - Creates a table structure with headers
   - Applies styling (colors, borders, fonts)
   - Handles page sizing and layout

### Temporary File Management

- Excel files are converted to temporary PDFs using Python's `tempfile` module
- Temporary files are created in the output folder's parent directory (or system temp)
- Files are automatically cleaned up after merging (using try/finally blocks)
- Cleanup occurs even if merging fails to prevent disk space issues

### PDF Read Error Suppression

- Some PDFs (especially Apple-annotated PDFs) generate noisy warnings during reading
- The system suppresses stderr during PDF reading operations
- Real errors are still caught and logged via exception handling
- Uses `strict=False` mode in pypdf to handle problematic PDFs gracefully

### Configuration Management

The application supports multiple configuration sources with a clear precedence order:

**Configuration Precedence** (highest to lowest):
1. **Environment Variables** - `PDF_MERGER_INPUT_FILE`, `PDF_MERGER_SOURCE_DIR`, `PDF_MERGER_OUTPUT_DIR`, `PDF_MERGER_COLUMN`
2. **CLI Arguments** - Command-line flags override config files
3. **User Config File** - `~/.pdf_merger/config.json` or `config.json` in app directory
4. **Per-Project Preset** - `.pdf_merger_config.json` in project directory (searched up directory tree)
5. **Defaults** - Built-in default values

**Configuration Components**:
- `config.py` - Main configuration management with precedence resolution
- `config_schema.py` - Schema validation and path validation
- All configuration values are validated (paths must exist, column names must be valid)
- Invalid values are logged as warnings and defaults are used

**Use Cases**:
- Environment variables for CI/CD and automated workflows
- CLI arguments for one-off operations
- User config file for personal defaults
- Per-project presets for project-specific settings

See `docs/CONFIGURATION.md` for detailed configuration documentation.

## Additional Resources

- **Installation Guide**: See `INSTALLATION.md`
- **Testing Guide**: See `TESTING.md`
- **User Guide**: See `docs/README_USER.md`
- **Configuration Guide**: See `docs/CONFIGURATION.md`
- **Build Guide**: See `BUILD.md` for packaging instructions
- **License Tools**: See `tools/README.md` for license generation

---

## Version

Current version: **1.0.0**

### Recent Changes (v1.0.0)

- Added Excel file support (.xlsx, .xls)
- Excel files automatically converted to PDF before merging
- Support for mixed merges (PDF + Excel combinations)
- Updated UI to reflect "Source Directory" instead of "PDF Directory"
- Improved error handling and logging
- Suppressed noisy PDF read warnings
- Updated dependencies: replaced xlsx2pdf with openpyxl + reportlab
