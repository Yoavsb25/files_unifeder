# PDF Batch Merger - Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Structure](#component-structure)
4. [Data Flow](#data-flow)
5. [Architecture Principles](#architecture-principles)
6. [Detailed Diagrams](#detailed-diagrams)
   - [Configuration Management](#configuration-management)
   - [Domain Models](#domain-models)
   - [Matching Rules](#matching-rules)
   - [Processing Pipeline](#processing-flow)
   - [Observability](#observability)
   - [Cross-Platform Path Handling](#cross-platform-path-handling)
   - [License Validation](#license-validation)

---

## Overview

PDF Batch Merger is a desktop application built with Python that merges multiple PDF and Excel files into PDF documents based on instructions from CSV or Excel files. The application follows a modular architecture with clear separation of concerns between business logic, user interface, and data processing.

### Key Features

- **GUI Application**: Built with CustomTkinter for a modern, cross-platform interface
- **License Management**: RSA-signed license validation system with offline mode, clock skew tolerance, and expiry warnings
- **Modular Design**: Clean separation between core logic, UI, and utilities
- **Comprehensive Testing**: Full test coverage with pytest
- **Multiple Input Formats**: Supports CSV and Excel files
- **Mixed File Support**: Can merge PDF and Excel files together (Excel files are converted to PDF)
- **Formal Matching Rules**: Deterministic file matching with ambiguity detection and Unicode normalization
- **Configuration Management**: Multi-source configuration with precedence (env vars > config > presets > defaults)
- **Domain Models**: Explicit type-safe models for rows, jobs, and results
- **Cross-Platform Support**: Handles Windows/macOS path differences (case sensitivity, Unicode, long paths)
- **Memory Efficiency**: Streaming mode for large PDF merging
- **Excel Rendering**: Pagination support for wide tables with auto-sizing
- **Observability**: Opt-in metrics, telemetry, and crash reporting

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        GUI[GUI Application<br/>CustomTkinter]
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
        Config[Configuration<br/>Multi-Source Precedence]
        Observability[Observability<br/>Metrics/Telemetry/Crash]
        PathUtils[Path Utils<br/>Cross-Platform]
    end
    
    subgraph "Domain Models"
        Models[Domain Models<br/>Row/Job/Result]
    end
    
    subgraph "Matching System"
        Matching[Matching Rules<br/>Formal Spec]
    end
    
    GUI --> Main
    Main --> License
    License --> Core
    Core --> Processor
    Processor --> Validator
    Processor --> FileReader
    Processor --> DataParser
    Processor --> PDFOps
    Processor --> ExcelConv
    Processor --> Logger
    Processor --> Models
    Processor --> Observability
    Processor --> Matching
    ExcelConv --> PDFOps
    Validator --> Exceptions
    FileReader --> Exceptions
    PDFOps --> Exceptions
    PDFOps --> PathUtils
    PDFOps --> Matching
    Main --> Config
    Main --> Observability
    GUI --> Config
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
│   ├── __init__.py              # Public API exports (run_merge, run_merge_job, load_config, etc.)
│   │
│   ├── config/                  # Configuration
│   │   ├── config_manager.py    # Configuration loading with precedence (env > user config > preset > defaults)
│   │   └── config_schema.py     # Schema and validation
│   │
│   ├── core/                    # Business logic and orchestration
│   │   ├── merge_orchestrator.py  # UI-facing API, job construction, row loading (orchestrator)
│   │   ├── merge_processor.py    # Job execution and row-level logic (processor)
│   │   ├── constants.py         # Shared constants
│   │   ├── csv_excel_reader.py  # CSV/Excel file reading
│   │   ├── serial_number_parser.py  # Serial number parsing
│   │   ├── result_reporter.py   # Result formatting
│   │   └── enums.py             # Shared enums
│   │
│   ├── models/                  # Domain models
│   │   ├── row.py               # Row data model
│   │   ├── merge_job.py         # Merge job model
│   │   └── merge_result.py      # Merge result model
│   │
│   ├── matching/                # Matching rules
│   │   ├── rules.py             # Formal matching rules
│   │   └── spec.md              # Matching specification
│   │
│   ├── operations/              # File-format operations
│   │   ├── pdf_merger.py        # PDF finding and merging
│   │   ├── streaming_pdf_merger.py  # Streaming PDF operations
│   │   └── excel_to_pdf_converter.py  # Excel to PDF conversion
│   │
│   ├── utils/                   # Utilities
│   │   ├── path_utils.py        # Cross-platform path handling
│   │   ├── validators.py        # Input validation
│   │   ├── exceptions.py        # Custom exception classes
│   │   └── logging_utils.py     # Logging configuration
│   │
│   ├── observability/           # Observability features
│   │   ├── metrics.py          # Metrics collection
│   │   ├── telemetry.py        # Telemetry (opt-in)
│   │   └── crash_reporting.py   # Crash reporting (opt-in)
│   │
│   ├── ui/                      # User interface
│   │   ├── app.py               # CustomTkinter GUI application
│   │   ├── handlers.py          # Event handlers (merge, file selection)
│   │   ├── components.py       # Reusable UI components
│   │   ├── theme.py             # Theme and styling
│   │   ├── license_ui.py        # License display helpers
│   │   └── __init__.py
│   │
│   └── licensing/               # License management
│       ├── license_manager.py   # License validation with UX improvements
│       ├── license_model.py     # License data model with expiry warnings
│       └── license_signer.py   # RSA signing/verification
│
├── tests/                       # Test suite
│   └── unit/                    # Unit tests by package
│       ├── config/              # test_config_manager.py, test_config_schema.py
│       ├── core/                # test_merge_processor.py, test_merge_orchestrator.py, etc.
│       ├── operations/          # test_pdf_merger.py, test_excel_to_pdf_converter.py, etc.
│       ├── ui/                  # test_app.py, test_components.py, test_handlers.py, etc.
│       ├── models/              # test_row.py, test_merge_job.py, test_merge_result.py
│       ├── utils/               # test_validators.py, test_exceptions.py, etc.
│       ├── licensing/           # test_license_manager.py, etc.
│       ├── matching/            # test_rules.py
│       └── observability/       # test_metrics.py, etc.
│
├── tools/                       # Development tools
│   └── license_generator.py    # License generation tool
│
└── requirements.txt             # Python dependencies
```

### Core Components

#### 1. Entry Point (`main.py`)

- **Responsibility**: Application bootstrap, observability initialization, and license checking
- **Flow**: 
  1. Initialize logging
  2. Load configuration
  3. Initialize observability (metrics, telemetry, crash reporting - opt-in)
  4. Check license status with expiry warnings
  5. Launch GUI if license valid
- **License manager injection**: main.py validates the license once and passes the `LicenseManager` instance into `run_gui(..., license_manager=...)` so the GUI does not re-validate; this pattern avoids double validation and is documented in the [UI Module](#8-ui-module-pdf_mergerui) section.
  6. Handle license errors gracefully with actionable messages

```mermaid
flowchart TD
    Start([Application Start]) --> Init[Initialize Logging]
    Init --> CheckLicense[Check License Status]
    CheckLicense --> Valid{License Valid?}
    Valid -->|Yes| LaunchGUI[Launch GUI]
    Valid -->|Expired| ShowError[Show Error<br/>Exit Application]
    Valid -->|Invalid| ShowError[Show Error<br/>Exit Application]
    LaunchGUI --> End([Application Running])
    ShowError --> Exit([Exit])
```

#### 2. Core Module (`pdf_merger/core/`)

**Orchestrator vs processor split:** The orchestrator (`merge_orchestrator.py`) is the UI-facing API and handles job construction and row loading; the processor (`merge_processor.py`) handles job execution and row-level logic.

- **`merge_orchestrator.py`**: UI-facing API and job construction
  - `run_merge()`: Legacy entry point (returns `ProcessingResult`)
  - `run_merge_job()`: Recommended entry point (returns `MergeResult`); builds `MergeJob`, loads rows from file, then delegates to processor
  - Single source for default column: uses `Constants.DEFAULT_SERIAL_NUMBERS_COLUMN` from `constants.py`

- **`merge_processor.py`**: Job execution and row-level logic
  - `process_file()`: Process entire CSV/Excel file (legacy, backward compatible)
  - `process_job()`: Process `MergeJob` using domain models (recommended)
  - `process_row_with_models()`: Process single row using `Row` model
  - Returns `MergeResult` with detailed per-row results

- **`result_reporter.py`**: Result formatting for display (summary and detailed reports)

#### 3. Processor (`pdf_merger/core/merge_processor.py`)

- **Responsibility**: Job execution and row-level processing using domain models
- **Key Functions**:
  - `process_file()`: Process entire CSV/Excel file (legacy, backward compatible)
  - `process_job()`: Process MergeJob using domain models (recommended)
  - `process_row_with_models()`: Process single row using Row model
  - Returns `MergeResult` with detailed per-row results
- **Domain Model Integration**:
  - Uses `Row`, `MergeJob`, and `MergeResult` models for type safety
  - Tracks detailed results per row (files found, missing, processing time)
  - Supports ambiguous match detection with configurable behavior
- **Observability Integration**:
  - Records metrics (processing time, file sizes, success rates, ambiguous matches)
  - Tracks counters and timers for performance analysis
- **Excel Handling**:
  - Finds both PDF and Excel files using formal matching rules (via `operations/pdf_merger.py`)
  - Converts Excel files to temporary PDFs using `convert_excel_to_pdf()` from `operations/excel_to_pdf_converter.py`
  - Merges all PDFs (original + converted Excel PDFs) with streaming support
  - Automatically cleans up temporary PDF files after merging
  - Handles conversion errors gracefully (logs and continues with other files)

#### 4. Validators (`pdf_merger/utils/validators.py`)

- **Responsibility**: Input validation
- **Validates**:
  - File existence and format
  - Folder existence
  - Required columns in data files
  - Serial number format (GRNW_ prefix)
  - Complete path sets

#### 5. File Reader (`pdf_merger/core/csv_excel_reader.py`)

- **Responsibility**: Reading CSV and Excel files
- **Features**:
  - Auto-detects file type (.csv, .xlsx, .xls)
  - Auto-detects CSV delimiter (comma, semicolon, tab)
  - Unified interface for all file types
  - Returns iterable of row data (dicts)

#### 6. Serial Number Parser (`pdf_merger/core/serial_number_parser.py`)

- **Responsibility**: Parsing serial numbers from strings
- **Features**:
  - Handles comma-separated values
  - Strips whitespace
  - Validates format (used by `Row.from_raw_data` and validators)

#### 7. PDF Operations (`pdf_merger/operations/pdf_merger.py`)

- **Responsibility**: PDF file operations with streaming support. File finding uses [matching rules](pdf_merger/matching/rules.py); see the [Matching Rules](#matching-rules) section.
- **Features**:
  - `find_source_file()`: Uses formal matching rules with ambiguity detection
  - `find_pdf_file()`: Case-insensitive PDF finding (backward compatibility)
  - `merge_pdfs()`: Merging multiple PDFs with automatic streaming for large files
  - Lazy loading of PDF libraries (pypdf)
  - Suppresses noisy PDF read warnings (Apple-annotated PDFs)
- **Streaming Support**:
  - Auto-detects large files and uses streaming mode
  - Processes pages incrementally to conserve memory
  - Configurable threshold (default: 100 MB estimated memory usage)
- **Matching Integration**:
  - Uses formal matching rules from `matching/rules.py`
  - Supports configurable ambiguity handling (FAIL_FAST, WARN_FIRST, LOG_ALL)
  - Unicode normalization for cross-platform compatibility
- **Implementation Details**:
  - Uses `strict=False` mode for pypdf to handle problematic PDFs
  - Suppresses stderr during PDF reading to avoid noisy warnings
  - Handles PdfReadError exceptions gracefully
  - Supports both pypdf and PyPDF2 libraries (with pypdf preferred)
  - Cross-platform path handling via `utils/path_utils.py`

#### 7b. PDF Streaming Operations (`pdf_merger/operations/streaming_pdf_merger.py`)

- **Responsibility**: Memory-efficient PDF merging for large files
- **Features**:
  - `merge_pdfs_streaming()`: Processes pages in chunks
  - `should_use_streaming()`: Auto-detects when streaming is needed
  - `estimate_memory_usage()`: Estimates memory requirements
- **Performance**:
  - Processes pages incrementally (default: 10 pages per chunk)
  - Reduces memory footprint for large PDFs
  - Progress logging for files with >100 pages

#### 7a. Excel Converter (`pdf_merger/operations/excel_to_pdf_converter.py`)

- **Responsibility**: Converting Excel files to PDF format with advanced rendering
- **Features**:
  - `convert_excel_to_pdf()`: Converts .xlsx and .xls files to PDF
  - Uses openpyxl to read Excel files and reportlab to generate PDFs
  - Handles empty cells and None values gracefully
  - Creates formatted PDF tables from Excel data
  - Supports both .xlsx and .xls formats (note: openpyxl primarily supports .xlsx)
- **Advanced Features**:
  - **Pagination**: Automatically splits wide tables across multiple pages
  - **Auto-sizing**: Calculates optimal column widths based on content
  - **Configurable page size**: Supports letter, A4, and custom sizes
  - **Orientation support**: Portrait and landscape modes
  - **Improved fidelity**: Enhanced fonts, colors, borders, and alternating row colors
- **Dependencies**:
  - `openpyxl>=3.0.0` - Excel file reading
  - `reportlab>=3.6.0` - PDF generation
- **Implementation Details**:
  - Reads all worksheets in order; empty sheets produce a blank page
  - Converts data to a formatted PDF table with headers
  - Constrains table width to usable page width; cell text wrapped via Paragraph for large tables
  - Handles styling (headers, borders, colors, alternating rows)
  - Preserves data structure in PDF format
  - Splits tables wider than 8 columns (configurable) across pages

#### 8. UI Module (`pdf_merger/ui/`)

- **Responsibility**: GUI application with configuration integration
- **Technology**: CustomTkinter
- **License manager injection**: `run_gui()` (in app.py) accepts an optional `license_manager` argument; main.py validates the license once and passes the manager in so the GUI does not re-validate.
- **Features**:
  - File/folder selection dialogs
  - Real-time progress logging
  - Result display
  - License status indicator with expiry warnings
  - Configuration loading (pre-populates fields from config)
  - Updated labels: "Source Directory" (supports PDF and Excel files)
- **License UX**:
  - Shows expiry warnings (critical/warning/info based on days remaining)
  - Displays days until expiry
  - Color-coded status (green/yellow/orange/red)
  - Offline mode detection
- **Configuration Integration**:
  - Loads configuration on startup
  - Pre-populates file/directory fields from config
  - Supports all configuration sources (env vars, config files, presets)
- **UI Updates**:
  - Changed "PDF Directory" to "Source Directory" to reflect Excel support
  - Updated dialog titles and validation messages
  - Shows Excel conversion progress in logs

#### 9. Licensing System (`pdf_merger/licensing/`)

- **`license_manager.py`**: License validation with enhanced UX
  - Offline mode detection
  - Clock skew tolerance (configurable, default ±5 minutes)
  - Expiry warning messages (30/14/7 days before expiry)
  - Actionable error messages
  - License refresh mechanism
- **`license_model.py`**: License data structure with expiry utilities
  - `days_until_expiry()`: Calculates days until license expires
  - `get_expiry_warning_level()`: Returns warning level (critical/warning/info)
  - `is_expired()`: Checks expiration with clock skew tolerance
- **`license_signer.py`**: RSA signature generation and verification

#### License System Architecture

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

#### License Validation Flow with UX Improvements

```mermaid
flowchart TD
    Start([Application Start]) --> LoadLicense[Load License File<br/>from App Dir or ~/.pdf_merger]
    LoadLicense --> CheckExists{License<br/>Exists?}
    CheckExists -->|No| NotFound[Status: NOT_FOUND<br/>Show Error Message]
    CheckExists -->|Yes| CheckOffline[Check Offline Mode<br/>Test Network Connection]
    CheckOffline -->|Offline| OfflineNote[Add Offline Note<br/>to Error Messages]
    CheckOffline -->|Online| CheckVersion
    OfflineNote --> CheckVersion[Check Version<br/>Match?]
    CheckVersion -->|No| VersionMismatch[Status: VERSION_MISMATCH<br/>Show Error Message]
    CheckVersion -->|Yes| VerifySignature[Verify RSA Signature<br/>Using Public Key]
    VerifySignature -->|Invalid| InvalidSig[Status: INVALID_SIGNATURE<br/>Show Error Message]
    VerifySignature -->|Valid| CheckExpiry[Check Expiration<br/>with Clock Skew Tolerance<br/>Default: ±5 minutes]
    CheckExpiry -->|Expired| Expired[Status: EXPIRED<br/>Show Expiry Message]
    CheckExpiry -->|Valid| CheckExpiryWarning{Expiring<br/>Soon?}
    CheckExpiryWarning -->|30 days| InfoWarning[Show Info Warning<br/>Days until expiry]
    CheckExpiryWarning -->|14 days| WarningLevel[Show Warning<br/>Consider renewing]
    CheckExpiryWarning -->|7 days| CriticalWarning[Show Critical Warning<br/>Renew soon]
    CheckExpiryWarning -->|>30 days| ValidLicense[Status: VALID<br/>Show License Info]
    InfoWarning --> ValidLicense
    WarningLevel --> ValidLicense
    CriticalWarning --> ValidLicense
    ValidLicense --> UpdateUI[Update UI<br/>Color-coded Status]
    NotFound --> ShowError[Show Error Message<br/>Actionable Guidance]
    VersionMismatch --> ShowError
    InvalidSig --> ShowError
    Expired --> ShowError
    UpdateUI --> End([Application Ready])
    ShowError --> Exit([Exit Application])
```

---

## Data Flow

### Processing Flow

#### Complete Processing Pipeline with Domain Models

```mermaid
flowchart TD
    Start([User Clicks Run Merge]) --> LoadConfig[Load Configuration<br/>with Precedence]
    LoadConfig --> Validate[Validate Inputs]
    Validate -->|Invalid| Error[Show Error]
    Validate -->|Valid| CreateJob[Create MergeJob<br/>Domain Model]
    CreateJob --> ReadFile[FileReader.read_data_file]
    ReadFile --> ParseRow[Row.from_raw_data<br/>Parse & Validate Serial Numbers]
    ParseRow --> AddRow[MergeJob.add_row]
    AddRow --> MoreRows{More Rows?}
    MoreRows -->|Yes| ParseRow
    MoreRows -->|No| ProcessJob[process_job<br/>MergeJob]
    ProcessJob --> InitMetrics[Initialize Metrics<br/>Collector]
    InitMetrics --> ProcessRow[process_row_with_models<br/>Row]
    ProcessRow --> StartTimer[Start Processing Timer]
    StartTimer --> FindFiles[find_source_file<br/>Using Matching Rules]
    FindFiles --> CheckAmbiguous{Ambiguous<br/>Match?}
    CheckAmbiguous -->|Yes| HandleAmbiguous{Behavior<br/>Mode?}
    CheckAmbiguous -->|No| CheckFound{Files<br/>Found?}
    HandleAmbiguous -->|FAIL_FAST| RaiseError[Raise ValueError]
    HandleAmbiguous -->|WARN_FIRST| LogWarning[Log Warning<br/>Use First Match]
    HandleAmbiguous -->|LOG_ALL| LogAll[Log All Matches]
    LogWarning --> CheckFound
    LogAll --> CheckFound
    CheckFound -->|No| SkipRow[RowResult: SKIPPED<br/>No Files Found]
    CheckFound -->|Yes| CheckExcel{Excel<br/>Files?}
    CheckExcel -->|Yes| ConvertExcel[convert_excel_to_pdf<br/>with Pagination]
    CheckExcel -->|No| CheckStreaming
    ConvertExcel --> CreateTemp[Create Temp PDF]
    CreateTemp --> CheckStreaming{Use<br/>Streaming?}
    CheckStreaming -->|Yes| StreamMerge[merge_pdfs_streaming<br/>Chunked Processing]
    CheckStreaming -->|No| StandardMerge[merge_pdfs<br/>Standard Mode]
    StreamMerge --> SavePDF[Save Merged PDF]
    StandardMerge --> SavePDF
    SavePDF --> RecordMetrics[Record Metrics<br/>Time, Size, Success]
    RecordMetrics --> CreateResult[RowResult: SUCCESS<br/>with Details]
    SavePDF --> Cleanup[Cleanup Temp Files]
    Cleanup --> AddResult[MergeResult.add_row_result]
    SkipRow --> AddResult
    CreateResult --> AddResult
    RaiseError --> AddResult
    AddResult --> NextRow{More Rows?}
    NextRow -->|Yes| ProcessRow
    NextRow -->|No| FinalMetrics[Final Metrics Summary]
    FinalMetrics --> ReturnResult[Return MergeResult<br/>with All Statistics]
    ReturnResult --> Display[Display Results in UI]
    Error --> End([End])
    Display --> End
```

### File Processing Pipeline

#### Enhanced Processing Pipeline with All Features

```mermaid
graph TB
    subgraph "Input"
        CSV[CSV/Excel File<br/>serial_numbers column]
        SourceFiles[Source Files Folder<br/>PDF & Excel]
        Config[Configuration<br/>Multi-Source]
    end
    
    subgraph "Processing"
        Read[File Reader<br/>Detect Type & Read]
        Parse[Data Parser<br/>Parse Serial Numbers]
        CreateRow[Create Row<br/>Domain Model]
        Find[Matching Rules<br/>Find Source Files<br/>with Ambiguity Detection]
        PathUtils[Path Utils<br/>Cross-Platform<br/>Normalization]
        Convert[Excel Converter<br/>Convert Excel to PDF<br/>with Pagination]
        CheckSize{File Size<br/>> Threshold?}
        StreamMerge[Streaming Merge<br/>Chunked Processing]
        StandardMerge[Standard Merge<br/>In-Memory]
        Metrics[Record Metrics<br/>Time, Size, Success]
    end
    
    subgraph "Output"
        Merged[Merged PDFs<br/>merged_row_N.pdf]
        Log[Processing Log<br/>Summary & Errors]
        Results[MergeResult<br/>Domain Model<br/>with Statistics]
    end
    
    CSV --> Read
    Config --> Read
    Read --> Parse
    Parse --> CreateRow
    CreateRow --> Find
    SourceFiles --> Find
    Find --> PathUtils
    PathUtils --> Find
    Find --> Convert
    Convert --> CheckSize
    CheckSize -->|Yes| StreamMerge
    CheckSize -->|No| StandardMerge
    StreamMerge --> Metrics
    StandardMerge --> Metrics
    Metrics --> Cleanup[Cleanup Temp PDFs]
    Cleanup --> Merged
    Metrics --> Results
    Results --> Log
```

#### Excel Conversion with Pagination Flow

```mermaid
flowchart TD
    Start([Excel File]) --> LoadExcel[Load Excel with openpyxl]
    LoadExcel --> ForSheets[For Each Worksheet<br/>in Workbook Order]
    ForSheets --> MoreSheets{More<br/>Sheets?}
    MoreSheets -->|No| BuildPDF
    MoreSheets -->|Yes| PageBreak[Page Break<br/>if not first sheet]
    PageBreak --> CheckEmpty{Empty<br/>Sheet?}
    CheckEmpty -->|Yes| BlankPage[Add Blank Page]
    CheckEmpty -->|No| ReadData[Read All Rows<br/>from Sheet]
    BlankPage --> ForSheets
    ReadData --> CalculateWidths[Calculate Column Widths<br/>Auto-Size Based on Content]
    CalculateWidths --> CheckWide{Table Width<br/>> max_cols_per_page?}
    CheckWide -->|Yes| SplitTable[Split Table<br/>Across Multiple Pages]
    CheckWide -->|No| CreateTable[Create Single Table]
    SplitTable --> CreatePages[Create Multiple Tables<br/>One per Page]
    CreatePages --> StyleTables[Apply Styling<br/>Headers, Borders, Colors<br/>Alternating Rows]
    CreateTable --> StyleTables
    StyleTables --> ForSheets
    BuildPDF[Build PDF Document<br/>with reportlab]
    BuildPDF --> SavePDF[Save PDF File]
    SavePDF --> End([PDF Ready])
```

---

## Detailed Diagrams

This section provides comprehensive mermaid diagrams explaining the code structure, data flow, and system behavior in detail.

---

## Architecture Principles

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data processing
2. **Modularity**: Each module has a single, well-defined responsibility
3. **Testability**: Components are designed to be easily testable with mocks and domain models
4. **Extensibility**: New features can be added without modifying core logic (Excel support added without breaking existing PDF-only workflows)
5. **Error Handling**: Comprehensive exception hierarchy for clear error messages
6. **Logging**: Structured logging throughout for debugging and monitoring
7. **Backward Compatibility**: Existing functionality preserved when adding new features
8. **Resource Management**: Automatic cleanup of temporary files (Excel-to-PDF conversions)
9. **Type Safety**: Explicit domain models with type hints for better contracts
10. **Determinism**: Formal matching rules ensure consistent behavior across runs
11. **Cross-Platform**: Handles platform differences (case sensitivity, Unicode, long paths)
12. **Privacy-First**: All observability features are opt-in with anonymization
13. **Public API**: External code and integrations should use only symbols exported from the `pdf_merger` package root (`__all__` in `pdf_merger/__init__.py`); internal modules may change without notice.

---

## Technical Details

### Excel to PDF Conversion

The Excel converter uses a two-step process:

1. **Reading**: Uses `openpyxl` to read Excel files (.xlsx format)
   - Converts all worksheets (tabs) in workbook order; each sheet starts on a new page
   - Empty sheets produce a blank page in the PDF
   - Handles empty cells (converts None to empty strings)
   - Preserves data structure

2. **PDF Generation**: Uses `reportlab` to create formatted PDFs
   - Creates a table structure with headers
   - Table width is constrained to the document's usable width (`doc.width`) so large tables fit on the page
   - Cell content is wrapped using ReportLab `Paragraph` so long text wraps within columns
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

#### Configuration Precedence Flow

```mermaid
flowchart TD
    Start([Application Start]) --> LoadDefaults[Load Defaults]
    LoadDefaults --> CheckPreset{Per-Project<br/>Preset Exists?}
    CheckPreset -->|Yes| LoadPreset[Load .pdf_merger_config.json<br/>from project directory]
    CheckPreset -->|No| CheckUserConfig
    LoadPreset --> CheckUserConfig{User Config<br/>File Exists?}
    CheckUserConfig -->|Yes| LoadUserConfig[Load ~/.pdf_merger/config.json<br/>or app/config.json]
    CheckUserConfig -->|No| CheckEnv
    LoadUserConfig --> CheckEnv{Environment<br/>Variables Set?}
    CheckEnv -->|Yes| ApplyEnv[Apply Environment Variables<br/>PDF_MERGER_*]
    CheckEnv -->|No| FinalConfig
    ApplyEnv --> FinalConfig[Final Configuration<br/>Merged with Precedence]
    FinalConfig --> Validate[Validate Configuration<br/>Check Paths & Values]
    Validate -->|Invalid| UseDefaults[Use Defaults for<br/>Invalid Values]
    Validate -->|Valid| UseConfig[Use Validated Config]
    UseDefaults --> UseConfig
    UseConfig --> End([Configuration Ready])
```

#### Configuration Resolution Process

```mermaid
graph LR
    subgraph "Configuration Sources"
        Env[Environment Variables<br/>Highest Priority]
        UserConfig[User Config File<br/>~/.pdf_merger/config.json]
        Preset[Per-Project Preset<br/>.pdf_merger_config.json]
        Defaults[Default Values<br/>Lowest Priority]
    end
    
    subgraph "Resolution"
        Merge[Merge with Precedence<br/>Higher Overrides Lower]
        Validate[Validate Values<br/>Paths, Column Names]
    end
    
    subgraph "Result"
        Final[Final AppConfig<br/>Ready to Use]
    end
    
    Env --> Merge
    UserConfig --> Merge
    Preset --> Merge
    Defaults --> Merge
    Merge --> Validate
    Validate --> Final
```

**Configuration Precedence** (highest to lowest):
1. **Environment Variables** - `PDF_MERGER_INPUT_FILE`, `PDF_MERGER_SOURCE_DIR`, `PDF_MERGER_OUTPUT_DIR`, `PDF_MERGER_COLUMN`
2. **User Config File** - `~/.pdf_merger/config.json` or `config.json` in app directory
3. **Per-Project Preset** - `.pdf_merger_config.json` in project directory (searched up directory tree)
4. **Defaults** - Built-in default values

**Configuration Components**:
- `config/config_manager.py` - Main configuration management with precedence resolution (`load_config`, `AppConfig`, `save_config`)
- `config/config_schema.py` - Schema validation and path validation
- All configuration values are validated (paths must exist, column names must be valid)
- Invalid values are logged as warnings and defaults are used
- Supports observability settings (metrics, telemetry, crash reporting)
- Supports matching behavior configuration (fail_on_ambiguous_matches)

**Use Cases**:
- Environment variables for CI/CD and automated workflows
- User config file for personal defaults
- Per-project presets for project-specific settings

See `docs/CONFIGURATION.md` for detailed configuration documentation.

### Domain Models

The application uses explicit domain models for type safety and better contracts:

#### Domain Model Relationships

```mermaid
classDiagram
    class Row {
        +int row_index
        +dict raw_data
        +str serial_numbers_str
        +List[str] serial_numbers
        +str required_column
        +from_raw_data() Row
        +has_serial_numbers() bool
    }
    
    class MergeJob {
        +Path input_file
        +Path source_folder
        +Path output_folder
        +str required_column
        +List[Row] rows
        +str job_id
        +dict metadata
        +create() MergeJob
        +add_row(Row)
        +get_total_rows() int
    }
    
    class RowResult {
        +int row_index
        +RowStatus status
        +Path output_file
        +List[Path] files_found
        +List[str] files_missing
        +str error_message
        +float processing_time
        +is_success() bool
    }
    
    class MergeResult {
        +int total_rows
        +int successful_merges
        +List[int] failed_rows
        +List[int] skipped_rows
        +List[RowResult] row_results
        +str job_id
        +float total_processing_time
        +add_row_result(RowResult)
        +get_success_rate() float
    }
    
    class RowStatus {
        <<enumeration>>
        SUCCESS
        FAILED
        SKIPPED
        PARTIAL
    }
    
    MergeJob "1" --> "*" Row : contains
    MergeResult "1" --> "*" RowResult : contains
    RowResult --> RowStatus : uses
    Row --> MergeJob : processed by
    RowResult --> Row : result of
```

#### Domain Model Flow

```mermaid
flowchart TD
    Start([Input File]) --> ReadFile[FileReader.read_data_file]
    ReadFile --> CreateRow[Row.from_raw_data<br/>Parse & Validate Serial Numbers]
    CreateRow --> AddToJob[MergeJob.add_row]
    AddToJob --> MoreRows{More Rows?}
    MoreRows -->|Yes| CreateRow
    MoreRows -->|No| ProcessJob[process_job<br/>MergeJob]
    ProcessJob --> ProcessRow[process_row_with_models<br/>Row]
    ProcessRow --> CreateResult[RowResult<br/>Status, Files, Time]
    CreateResult --> AddResult[MergeResult.add_row_result]
    AddResult --> MoreRows2{More Rows?}
    MoreRows2 -->|Yes| ProcessRow
    MoreRows2 -->|No| FinalResult[MergeResult<br/>Complete Statistics]
    FinalResult --> End([Return Results])
```

**Models** (`pdf_merger/models/`):
- **`Row`**: Represents a single row from input data
  - Parses and validates serial numbers
  - Tracks raw data and normalized serial numbers
  - Provides validation methods
- **`MergeJob`**: Represents a complete merge job
  - Contains input file, source folder, output folder
  - Tracks all rows to process
  - Supports job metadata and identifiers
- **`MergeResult`**: Detailed result of processing
  - Per-row results with status (SUCCESS, FAILED, SKIPPED, PARTIAL)
  - Tracks files found, files missing, processing times
  - Provides success rate calculations
  - Backward compatible with legacy `ProcessingResult`

**Benefits**:
- Type safety throughout the codebase
- Clear contracts between components
- Better testability with explicit models
- Detailed result tracking for debugging

### Matching Rules

The application uses formal matching rules for deterministic file finding:

#### Matching Algorithm Flow

```mermaid
flowchart TD
    Start([Serial Number Input]) --> Normalize[Normalize Unicode<br/>NFC Normalization]
    Normalize --> LowerCase[Convert to Lowercase]
    LowerCase --> SearchDir[Search Directory<br/>Iterate All Files]
    SearchDir --> CheckExt{File Extension<br/>Supported?}
    CheckExt -->|No| NextFile[Next File]
    CheckExt -->|Yes| ExactMatch{Exact Match?<br/>Case-Insensitive}
    ExactMatch -->|Yes| AddExact[Add to Exact Matches<br/>Confidence: EXACT]
    ExactMatch -->|No| StemMatch{Stem Match?<br/>Filename without Extension}
    StemMatch -->|Yes| AddStem[Add to Stem Matches<br/>Confidence: STEM]
    StemMatch -->|No| NextFile
    AddExact --> SortMatches[Sort All Matches<br/>Alphabetically by Full Path]
    AddStem --> SortMatches
    NextFile --> MoreFiles{More Files?}
    MoreFiles -->|Yes| CheckExt
    MoreFiles -->|No| SortMatches
    SortMatches --> CheckAmbiguous{Multiple<br/>Matches?}
    CheckAmbiguous -->|Yes| AmbiguousBehavior{Behavior<br/>Mode?}
    CheckAmbiguous -->|No| ReturnMatch[Return Single Match]
    AmbiguousBehavior -->|FAIL_FAST| RaiseError[Raise ValueError<br/>Prevent Silent Wrong Merge]
    AmbiguousBehavior -->|WARN_FIRST| LogWarning[Log Warning<br/>Use First Match]
    AmbiguousBehavior -->|LOG_ALL| LogAll[Log All Matches<br/>Use First Match]
    LogWarning --> ReturnMatch
    LogAll --> ReturnMatch
    ReturnMatch --> End([Return MatchResult])
    RaiseError --> End
```

#### Matching Rules Decision Tree

```mermaid
graph TD
    Input[Filename: GRNW_12345] --> Step1[1. Try Exact Match<br/>Case-Insensitive]
    Step1 -->|Found| Exact[GRNW_12345.pdf<br/>GRNW_12345.xlsx<br/>Confidence: EXACT]
    Step1 -->|Not Found| Step2[2. Try Stem Match<br/>Filename without Extension]
    Step2 -->|Found| Stem[GRNW_12345_v2.pdf<br/>GRNW_12345_final.xlsx<br/>Confidence: STEM]
    Step2 -->|Not Found| NoMatch[No Match Found<br/>Return None]
    Exact --> Multiple{Multiple<br/>Matches?}
    Stem --> Multiple
    Multiple -->|Yes| Sort[Sort Alphabetically<br/>by Full Path]
    Multiple -->|No| Return[Return Match]
    Sort --> Behavior{Behavior<br/>Mode?}
    Behavior -->|FAIL_FAST| Error[Raise ValueError]
    Behavior -->|WARN_FIRST| Warn[Log Warning<br/>Use First]
    Behavior -->|LOG_ALL| Log[Log All<br/>Use First]
    Warn --> Return
    Log --> Return
```

**Matching System** (`pdf_merger/matching/`):
- **Formal Specification**: Documented matching algorithm with examples
- **Priority Order**:
  1. Exact match (case-insensitive, with any supported extension)
  2. Stem match (filename without extension)
  3. Deterministic tie-breaking (alphabetical by full path)
- **Unicode Normalization**: NFC normalization for cross-platform compatibility
- **Ambiguity Detection**: Detects when multiple files match
- **Configurable Behavior**:
  - `FAIL_FAST`: Raises error on ambiguous matches (production default)
  - `WARN_FIRST`: Warns and uses first match (development)
  - `LOG_ALL`: Logs all matches for debugging

**Performance**:
- O(n) complexity for directory scanning
- Lazy sorting (only when needed)
- Future: Indexing support for very large directories

See `pdf_merger/matching/spec.md` and `docs/MATCHING_RULES.md` for detailed specifications.

### Cross-Platform Path Handling

The application handles path differences between Windows, macOS, and Linux:

#### Path Handling Flow

```mermaid
flowchart TD
    Start([Path Input]) --> Resolve[Resolve to Absolute Path]
    Resolve --> NormalizeUnicode[Normalize Unicode<br/>NFC Normalization]
    NormalizeUnicode --> CheckPlatform{Platform?}
    CheckPlatform -->|Windows| WindowsPath[Case-Insensitive<br/>Comparison]
    CheckPlatform -->|macOS| MacPath[NFD to NFC<br/>Case-Sensitive]
    CheckPlatform -->|Linux| LinuxPath[Case-Sensitive<br/>NFC]
    WindowsPath --> CheckLong{Path Length<br/>> 260 chars?}
    MacPath --> ValidatePath[Validate Path<br/>Existence, Type]
    LinuxPath --> ValidatePath
    CheckLong -->|Yes| CheckLongEnabled{Long Path<br/>Enabled?}
    CheckLong -->|No| ValidatePath
    CheckLongEnabled -->|Yes| UseLongPath[Use Long Path Prefix<br/>\\\\?\\]
    CheckLongEnabled -->|No| WarnLong[Log Warning<br/>May Fail]
    UseLongPath --> ValidatePath
    WarnLong --> ValidatePath
    ValidatePath --> End([Normalized Path])
```

#### Cross-Platform Path Comparison

```mermaid
graph LR
    subgraph "Windows"
        WinPath1[C:\Users\Test\file.pdf]
        WinPath2[C:\users\test\FILE.PDF]
        WinCompare[Case-Insensitive<br/>Match: True]
    end
    
    subgraph "macOS"
        MacPath1[/Users/Test/café.pdf]
        MacPath2[/Users/Test/café.pdf]
        MacNormalize[NFC Normalization<br/>Both: café.pdf]
        MacCompare[Case-Sensitive<br/>Match: True]
    end
    
    subgraph "Linux"
        LinuxPath1[/home/user/file.pdf]
        LinuxPath2[/home/user/FILE.PDF]
        LinuxCompare[Case-Sensitive<br/>Match: False]
    end
    
    WinPath1 --> WinCompare
    WinPath2 --> WinCompare
    MacPath1 --> MacNormalize
    MacPath2 --> MacNormalize
    MacNormalize --> MacCompare
    LinuxPath1 --> LinuxCompare
    LinuxPath2 --> LinuxCompare
```

**Path Utilities** (`pdf_merger/utils/path_utils.py`):
- **Case Sensitivity**: Case-insensitive comparison on Windows, case-sensitive on Unix
- **Unicode Normalization**: NFC normalization (handles macOS NFD)
- **Long Path Support**: Detection and handling for Windows paths >260 characters
- **Path Validation**: Cross-platform path validation with existence checks

**Use Cases**:
- Consistent file matching across platforms
- Handling accented characters and special Unicode
- Supporting long file paths on Windows

### Observability

Observability features (metrics, telemetry, crash reporting) are **opt-in** and
**initialized at startup from config** (see main.py: load_config then observability
init). The flow is documented here for contributors.
The application includes opt-in observability features:

#### Observability Architecture

```mermaid
graph TB
    subgraph "Application Components"
        Processor[Processor]
        PDFOps[PDF Operations]
        ExcelConv[Excel Converter]
        Main[main.py]
    end
    
    subgraph "Observability Layer"
        Metrics[Metrics Collector<br/>Counters, Timers, Gauges]
        Telemetry[Telemetry Service<br/>Opt-in Anonymous Stats]
        CrashReporter[Crash Reporter<br/>Opt-in Stack Traces]
    end
    
    subgraph "Data Collection"
        MetricsData[Processing Time<br/>File Sizes<br/>Success Rates<br/>Ambiguous Matches]
        TelemetryData[Event Types<br/>System Info<br/>No Personal Data]
        CrashData[Stack Traces<br/>Context Info<br/>System Info]
    end
    
    Processor --> Metrics
    PDFOps --> Metrics
    ExcelConv --> Metrics
    Processor --> Telemetry
    Main --> CrashReporter
    Metrics --> MetricsData
    Telemetry --> TelemetryData
    CrashReporter --> CrashData
```

#### Observability Flow

```mermaid
flowchart TD
    Start([Application Start]) --> LoadConfig[Load Configuration]
    LoadConfig --> CheckMetrics{Metrics<br/>Enabled?}
    CheckMetrics -->|Yes| InitMetrics[Initialize Metrics Collector]
    CheckMetrics -->|No| CheckTelemetry
    InitMetrics --> CheckTelemetry{Telemetry<br/>Enabled?}
    CheckTelemetry -->|Yes| InitTelemetry[Initialize Telemetry Service]
    CheckTelemetry -->|No| CheckCrash
    InitTelemetry --> CheckCrash{Crash Reporting<br/>Enabled?}
    CheckCrash -->|Yes| InitCrash[Initialize Crash Reporter<br/>Install Exception Hook]
    CheckCrash -->|No| Process
    InitCrash --> Process[Process Merge Job]
    Process --> RecordCounter[Record Counter Metrics<br/>rows_successful<br/>files_found<br/>ambiguous_matches]
    Process --> RecordTimer[Record Timer Metrics<br/>row_processing_time<br/>job_processing_time]
    Process --> RecordGauge[Record Gauge Metrics<br/>output_file_size_mb<br/>job_success_rate]
    RecordCounter --> RecordEvent[Record Telemetry Event<br/>merge_completed]
    RecordTimer --> RecordEvent
    RecordGauge --> RecordEvent
    RecordEvent --> CheckException{Exception<br/>Occurred?}
    CheckException -->|Yes| ReportCrash[Report Crash<br/>Save Stack Trace]
    CheckException -->|No| FlushTelemetry[Flush Telemetry<br/>Events]
    ReportCrash --> FlushTelemetry
    FlushTelemetry --> GetSummary[Get Metrics Summary]
    GetSummary --> End([Observability Complete])
```

**Observability Package** (`pdf_merger/observability/`):
- **Metrics** (`metrics.py`):
  - Processing time per row
  - File sizes processed
  - Success/failure rates
  - Match ambiguity counts
  - Memory usage (if available)
- **Telemetry** (`telemetry.py`):
  - Opt-in anonymous usage statistics
  - No personal data collected
  - Session tracking (optional)
- **Crash Reporting** (`crash_reporting.py`):
  - Opt-in crash reporting with stack traces
  - Local crash report storage
  - Context information capture

**Privacy**:
- All observability features are opt-in (disabled by default)
- Telemetry is anonymized (no personal data)
- Crash reports stored locally (not automatically sent)
- Configurable via configuration system

### Excel Rendering Improvements

Enhanced Excel to PDF conversion with professional rendering:

**Features**:
- **Pagination**: Automatically splits wide tables across pages
- **Auto-sizing**: Calculates optimal column widths based on content
- **Page Configuration**: Supports letter, A4, portrait, landscape
- **Rendering Fidelity**:
  - Professional table styling
  - Alternating row colors
  - Header row highlighting
  - Grid lines and borders
  - Font and color preservation

**Configuration**:
- `max_cols_per_page`: Maximum columns per page (default: 8)
- `auto_size_columns`: Enable/disable auto-sizing (default: True)
- `page_size`: Page size selection (default: 'letter')
- `orientation`: Portrait or landscape (default: 'portrait')

## Additional Resources

- **Installation Guide**: See `INSTALLATION.md` (in same directory)
- **Testing Guide**: See `TESTING.md` (in same directory)
- **User Guide**: See `docs/README_USER.md`
- **Configuration Guide**: See `docs/CONFIGURATION.md`
- **Matching Rules**: See `docs/MATCHING_RULES.md` and `pdf_merger/matching/spec.md`
- **Packaging Guide**: See `docs/PACKAGING.md` for signing and notarization
- **Build Guide**: See `BUILD.md` for packaging instructions
- **License Tools**: See `tools/README.md` for license generation

---

## Version

Current version: **1.1.0**

### Recent Changes (v1.1.0)

**Major Enhancements:**
- **Configuration Management**: Multi-source configuration with precedence (env vars > config > presets > defaults)
- **Domain Models**: Explicit type-safe models (Row, MergeJob, MergeResult) for better contracts
- **Formal Matching Rules**: Deterministic file matching with ambiguity detection and Unicode normalization
- **Cross-Platform Path Handling**: Handles Windows/macOS differences (case sensitivity, Unicode, long paths)
- **PDF Streaming**: Memory-efficient merging for large PDFs with auto-detection
- **Excel Rendering**: Pagination support for wide tables with auto-sizing and improved fidelity
- **Observability**: Opt-in metrics, telemetry, and crash reporting with privacy controls
- **License UX**: Offline mode detection, clock skew tolerance, expiry warnings (30/14/7 days)

**Improvements:**
- Enhanced Excel to PDF conversion with professional styling
- Ambiguous match detection with configurable handling (FAIL_FAST, WARN_FIRST, LOG_ALL)
- License expiry warnings with color-coded UI indicators
- Configuration integration in GUI (pre-populates fields)
- Detailed per-row result tracking with processing times
- Memory usage monitoring and warnings

**Previous Version (v1.0.0):**
- Added Excel file support (.xlsx, .xls)
- Excel files automatically converted to PDF before merging
- Support for mixed merges (PDF + Excel combinations)
- Updated UI to reflect "Source Directory" instead of "PDF Directory"
- Improved error handling and logging
- Suppressed noisy PDF read warnings
- Updated dependencies: replaced xlsx2pdf with openpyxl + reportlab
