## PDF Batch Merger

[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macOS-blue.svg)](./)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](./requirements.txt)

**PDF Batch Merger** is a desktop application for **high‑volume document assembly**.  
It merges PDF and Excel files into final PDF bundles, driven by instructions in CSV/Excel control files.  
It is designed for **law firms, finance, and operations teams** that repeatedly build case files, deal books, or reporting packs.

> **At a glance**  
> - Spreadsheet in → fully assembled PDFs out  
> - Excel and PDF in the same pipeline  
> - Licensed, production‑grade desktop app

---

## Table of Contents

- [Why PDF Batch Merger?](#why-pdf-batch-merger)
- [Core Features](#core-features)
- [High‑Level Architecture](#high-level-architecture)
- [Installation & Setup](#installation--setup)
- [Running the Application (Development)](#running-the-application-development)
- [Input / Output Workflow Example](#input--output-workflow-example)
- [Licensing & License Generation](#licensing--license-generation)
- [Packaging & Distribution](#packaging--distribution)
- [Development & Testing](#development--testing)
- [Documentation Index](#documentation-index)
- [Support & Contact](#support--contact)

---

## Why PDF Batch Merger?

- **Save hours of manual work**: Turn rows in a spreadsheet into fully assembled PDFs in one run.
- **Excel + PDF in one pass**: Convert Excel sheets to PDF and merge them with existing PDFs.
- **Robust for production use**: Case‑insensitive matching, strong error handling, and a licensing system suitable for commercial distribution.
- **Cross‑platform desktop app**: Modern GUI built with `customtkinter`, packaged via PyInstaller for Windows and macOS.

---

## Core Features

- **Flexible batch merging**
  - Merge **multiple PDFs** into a single document.
  - Merge **Excel → PDF** (via `reportlab` and `openpyxl`) and combine with PDFs.
  - Support for **mixed rows** (e.g. `file1.pdf, file2.xlsx, file3.pdf`).

- **Spreadsheet‑driven workflows**
  - Control file in **CSV or Excel** format.
  - A dedicated `serial_numbers` (or similar) column defines **which files** to merge for each output row.
  - One row in the control file → one merged output PDF.

- **Production‑ready UX**
  - Source directory, input file, and output directory selected via GUI.
  - Progress feedback and improved error messages for missing or unreadable files.
  - Case‑insensitive file matching for predictable behavior across platforms.

- **Licensing & distribution**
  - **RSA‑signed license system** (`cryptography`‑based).
  - Separate **private key** (for license generation) and **public key** (embedded in the app).
  - License enforcement suitable for distributing to external clients.

---

## High‑Level Architecture

At a glance, the project is organized as follows:

```text
files_unifeder/
├── pdf_merger/               # Main application package
│   ├── core/                 # Core business logic (merging, file resolution, etc.)
│   ├── ui/                   # GUI (CustomTkinter)
│   ├── licensing/            # License validation and enforcement
│   ├── excel_converter.py    # Excel → PDF conversion
│   ├── pdf_operations.py     # PDF loading, merging, and low‑level operations
│   └── processor.py          # Orchestration of merge jobs
├── tools/                    # Developer tools (license generation, packaging helpers, etc.)
├── docs/                     # End‑user and architecture documentation
├── tests/                    # Unit and integration tests
└── requirements.txt          # Python dependencies
```

For a deeper architectural walkthrough, see `docs/ARCHITECTURE.md`.

---

## Installation & Setup

### Prerequisites

- **Python**: 3.8 or higher (3.11 recommended for development)
- **OS**: Windows or macOS (the packaged app targets these platforms)
- **Tools (for development)**:
  - Git
  - A virtual environment manager (e.g. `venv`, `pyenv`, `conda`)

### 1. Clone the repository

```bash
git clone https://github.com/<your-org-or-user>/files_unifeder.git
cd files_unifeder
```

### 2. Create & activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# or
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Dependencies (see `requirements.txt` for exact versions):

- `pypdf` – PDF reading and merging
- `pandas` – working with CSV/Excel control files
- `openpyxl` – Excel I/O
- `reportlab` – Excel → PDF rendering
- `customtkinter` – modern GUI
- `cryptography` – RSA license signing/verification
- `pyinstaller` – desktop packaging
- Google API libraries – optional Google Drive upload tooling

---

## Running the Application (Development)

From the project root:

```bash
python main.py
```

In the GUI:

1. Select the **input file** (CSV or Excel) that defines which files to merge.
2. Select the **source directory** containing your PDFs and Excel workbooks.
3. Select the **output directory** where merged PDFs will be written.
4. Click **Run Merge** and monitor progress.

> For detailed screenshots and end‑user flows, see `docs/README_USER.md`.

---

## Input / Output Workflow Example

### Example control file (`input.xlsx`)

```text
serial_numbers
GRNW_1, GRNW_2
GRNW_3.xlsx, GRNW_4.pdf
```

### Example source directory

- `GRNW_1.pdf`
- `GRNW_2.pdf`
- `GRNW_3.xlsx`
- `GRNW_4.pdf`

### Resulting outputs

- `merged_row_1.pdf` – `GRNW_1.pdf` + `GRNW_2.pdf`
- `merged_row_2.pdf` – `GRNW_3.xlsx` (converted to PDF) + `GRNW_4.pdf`

The application automatically:

- Resolves file names (case‑insensitively where appropriate).
- Converts Excel inputs to PDF.
- Concatenates PDFs into final bundles.

---

## Licensing & License Generation

PDF Batch Merger uses a **public/private key**-based licensing system:

- The application embeds a **public key** and validates license files (`license.json`).
- License files are **RSA‑signed** and cannot be modified without invalidating the signature.
- A separate **private key**, kept only by the vendor, is used to generate licenses.

### Generating keys (for vendors / maintainers)

From the project root:

```bash
python tools/license_generator.py generate-keys --output-dir tools
```

This will create:

- `tools/private_key.pem` – **keep this secret and never commit it**
- `tools/public_key.pem` – copy into `pdf_merger/licensing/public_key.pem`

See `tools/README.md` for detailed instructions and security notes.

### Generating a license

```bash
python tools/license_generator.py generate-license \
  --company "Example Client Ltd" \
  --expires "2027-12-31" \
  --machines 5 \
  --output license.json
```

Distribute `license.json` to the client.  
The client places it:

- Next to the application binary/bundle, **or**
- In their user license directory (e.g. `~/.pdf_merger/` or `%USERPROFILE%\.pdf_merger\` depending on OS).

---

## Packaging & Distribution

The repository includes configuration for building **platform‑specific installers/bundles** using PyInstaller and CI workflows.

- **Local builds**  
  See `docs/INSTALLATION.md` for exact commands and build options.

- **CI‑driven client packages**  
  The GitHub Actions workflow `.github/workflows/build-client-package.yml` can:
  - Build **Windows** and **macOS** client packages.
  - Inject a per‑client `license.json` during the build.
  - Zip the result and optionally upload to **Google Drive**.

This is suitable for generating **per‑client deliveries** with controlled licensing.

---

## Development & Testing

### Running tests

```bash
pytest                # run all tests
pytest --cov=pdf_merger --cov-report=html
```

See `docs/TESTING.md` for more details on test structure and conventions.

### Code layout (developer view)

- `pdf_merger/core` – core operations and business rules.
- `pdf_merger/ui` – CustomTkinter UI components and event handling.
- `pdf_merger/licensing` – license model, validation, and integration.
- `pdf_merger/excel_converter.py` – Excel → PDF pipeline.
- `pdf_merger/pdf_operations.py` – lower‑level PDF manipulation helpers.
- `pdf_merger/processor.py` – orchestration of full merge runs.

---

## Documentation Index

- **End‑User Guide**: `docs/README_USER.md`
- **Installation & Packaging**: `docs/INSTALLATION.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Testing Guide**: `docs/TESTING.md`
- **License Tools**: `tools/README.md`

---

## Support & Contact

PDF Batch Merger is intended to be distributed as a licensed product.  
For **licenses, commercial use, or technical support**, please contact your software provider or system integrator managing this deployment.

---

**Current application version**: `1.0.0`
