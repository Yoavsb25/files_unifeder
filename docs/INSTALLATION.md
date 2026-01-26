# PDF Batch Merger - Installation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step-by-Step Installation](#step-by-step-installation)
3. [Setting Up Development License](#setting-up-development-license)
4. [Running the Application](#running-the-application)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before installing PDF Batch Merger, ensure you have:

- **Python 3.6 or higher** (Python 3.14 recommended for tkinter support on macOS)
- **pip** (Python package manager) - usually comes with Python
- **Git** (for cloning the repository)
- **Homebrew** (macOS only, for installing Python with tkinter support)

---

## Step-by-Step Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd files_unifeder
```

### Step 2: Create Virtual Environment

It's recommended to use a virtual environment to isolate dependencies.

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Note for macOS users**: If you need tkinter support, use Python 3.14:
```bash
# Install Python 3.14 with tkinter via Homebrew
brew install python-tk@3.14

# Create venv with Python 3.14
python3.14 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages:
- `pypdf>=3.0.0` - PDF merging library
- `pandas>=1.3.0` - Data manipulation (for Excel files)
- `openpyxl>=3.0.0` - Excel file reading
- `reportlab>=3.6.0` - PDF generation (for Excel to PDF conversion)
- `customtkinter>=5.0.0` - Modern GUI framework
- `cryptography>=41.0.0` - License signing/verification
- `pytest>=7.0.0` - Testing framework (for development)
- `pytest-cov>=4.0.0` - Coverage reporting (for development)
- `pyinstaller>=6.0.0` - Application packaging (for building)

### Step 4: Verify Installation

Check that all dependencies installed correctly:

```bash
python -c "import pypdf, pandas, customtkinter, cryptography; print('All dependencies installed!')"
```

If you see "All dependencies installed!", you're ready to proceed.

---

## Setting Up Development License

For local development, you need to generate a license file. The application requires a valid license to run.

### Step 1: Generate RSA Key Pair

```bash
python tools/license_generator.py generate-keys --output-dir tools
```

This creates:
- `tools/private_key.pem` - **Keep this secret!** Used to sign licenses
- `tools/public_key.pem` - Embedded in the application for verification

### Step 2: Copy Public Key to Licensing Directory

```bash
cp tools/public_key.pem pdf_merger/licensing/public_key.pem
```

The application will use this public key to verify license signatures.

### Step 3: Create License Directory

```bash
mkdir -p ~/.pdf_merger
```

On Windows, use:
```bash
mkdir %USERPROFILE%\.pdf_merger
```

### Step 4: Generate Development License

```bash
python tools/license_generator.py generate-license \
    --company "Development" \
    --expires "2030-12-31" \
    --machines 10 \
    --private-key tools/private_key.pem \
    --output ~/.pdf_merger/license.json
```

On Windows, use:
```bash
python tools/license_generator.py generate-license ^
    --company "Development" ^
    --expires "2030-12-31" ^
    --machines 10 ^
    --private-key tools/private_key.pem ^
    --output %USERPROFILE%\.pdf_merger\license.json
```

This creates a development license valid until 2030 for 10 machines.

---

## Running the Application

### Basic Usage

Once installation is complete, run the application:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate      # Windows

# Run the application
python main.py
```

The GUI application should launch. You should see:
- License status indicator (green checkmark if valid)
- File selection buttons
- Run Merge button
- Log area

### Verifying License

When the application starts, it checks the license. You should see:
- **Green checkmark**: License is valid
- **Yellow warning**: License expired (app still runs but merge may be disabled)
- **Red error**: License invalid or not found

If you see license errors, ensure you completed the [Setting Up Development License](#setting-up-development-license) steps above.

---

## Troubleshooting

### Issue: "No module named '_tkinter'"

**Problem**: Python doesn't have tkinter support installed.

**Solution (macOS):**
```bash
# Install Python 3.14 with tkinter via Homebrew
brew install python-tk@3.14

# Remove old virtual environment
rm -rf .venv

# Create new venv with Python 3.14
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Solution (Linux):**
```bash
# Install tkinter package
sudo apt-get install python3-tk  # Debian/Ubuntu
# or
sudo yum install python3-tkinter  # CentOS/RHEL

# Then recreate venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Solution (Windows):**
Tkinter is usually included with Python on Windows. If missing, reinstall Python and ensure "tcl/tk" is selected during installation.

### Issue: "License file not found"

**Problem**: License file is missing or in wrong location.

**Solution:**
1. Verify license file exists:
   ```bash
   ls ~/.pdf_merger/license.json  # macOS/Linux
   dir %USERPROFILE%\.pdf_merger\license.json  # Windows
   ```

2. If missing, complete the [Setting Up Development License](#setting-up-development-license) steps.

3. Verify public key is in place:
   ```bash
   ls pdf_merger/licensing/public_key.pem
   ```

### Issue: "License signature is invalid"

**Problem**: Public key doesn't match the private key used to sign the license.

**Solution:**
1. Regenerate keys and license:
   ```bash
   # Remove old keys
   rm tools/private_key.pem tools/public_key.pem
   
   # Regenerate everything
   python tools/license_generator.py generate-keys --output-dir tools
   cp tools/public_key.pem pdf_merger/licensing/public_key.pem
   python tools/license_generator.py generate-license \
       --company "Development" \
       --expires "2030-12-31" \
       --machines 10 \
       --private-key tools/private_key.pem \
       --output ~/.pdf_merger/license.json
   ```

### Issue: Dependencies fail to install

**Problem**: pip or Python version issues.

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing with verbose output to see errors
pip install -r requirements.txt -v

# If specific package fails, install individually
pip install pypdf
pip install pandas
pip install openpyxl
pip install customtkinter
pip install cryptography
```

### Issue: "ModuleNotFoundError" when running

**Problem**: Virtual environment not activated or dependencies not installed.

**Solution:**
```bash
# Verify virtual environment is activated (should see .venv in prompt)
which python  # Should point to .venv/bin/python

# If not activated, activate it
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Application crashes on startup

**Problem**: Missing dependencies or configuration issues.

**Solution:**
1. Check Python version:
   ```bash
   python --version  # Should be 3.6 or higher
   ```

2. Verify all dependencies:
   ```bash
   pip list | grep -E "(pypdf|pandas|openpyxl|customtkinter|cryptography)"
   ```

3. Check for error messages in terminal output

4. Try running with verbose logging:
   ```bash
   python main.py --verbose
   ```

### Issue: GUI doesn't appear

**Problem**: Display or windowing system issues.

**Solution:**
1. Check if you're running in a headless environment (no display)
2. On Linux, ensure X11 or Wayland is running
3. On macOS, check System Preferences → Security & Privacy for display permissions
4. Try running from terminal to see error messages

---

## Next Steps

After successful installation:

1. **Read the User Guide**: See `docs/README_USER.md` for usage instructions
2. **Run Tests**: See `TESTING.md` (in same directory) for testing instructions
3. **Explore Architecture**: See `ARCHITECTURE.md` (in same directory) for system design
4. **Build Application**: See `BUILD.md` for packaging instructions

---

## Uninstallation

To remove the application:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv

# Remove license files (optional)
rm -rf ~/.pdf_merger  # macOS/Linux
rmdir /s %USERPROFILE%\.pdf_merger  # Windows

# Remove repository (if desired)
cd ..
rm -rf files_unifeder
```

---

## Version

Current version: **1.0.0**
