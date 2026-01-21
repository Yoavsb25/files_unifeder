# PDF Batch Merger - User Guide

## What It Does

PDF Batch Merger is a desktop application that automatically merges multiple PDF files based on instructions from a CSV or Excel file. It's designed for law firms and businesses that need to combine PDF documents in bulk.

## How to Use

### Step 1: Prepare Your Files

1. **Input File**: Create a CSV or Excel file with a column named `serial_numbers`. Each row should contain the filenames of PDFs you want to merge, separated by commas.
   - Example: `GRNW_12345, GRNW_67890, GRNW_11111`

2. **PDF Folder**: Place all your PDF files in a single folder. The application will search this folder for the files listed in your input file.

3. **Output Folder**: Choose or create a folder where the merged PDFs will be saved.

### Step 2: Run the Application

1. Double-click the **PDF Batch Merger** application to launch it.

2. The application will check your license. If your license is valid, you'll see a green checkmark at the top.

3. Use the **Browse** buttons to select:
   - Your CSV/Excel input file
   - The folder containing your PDF files
   - The folder where merged PDFs should be saved

4. Click the **Run Merge** button to start processing.

5. Watch the progress in the log area. The application will show:
   - Which files are being processed
   - Which PDFs were found
   - Any warnings or errors
   - A summary when complete

### Step 3: Check Results

- Merged PDFs are saved in your output folder with names like `merged_row_1.pdf`, `merged_row_2.pdf`, etc.
- The log area shows a summary of how many rows were processed successfully.

## Common Issues

### "License expired" or "License not found"

- Contact support to obtain or renew your license file.
- Place the `license.json` file in the same folder as the application.

### "PDF file not found"

- The application searches for PDFs by filename (case-insensitive).
- Make sure the filenames in your CSV/Excel file match the actual PDF filenames.
- Check that all PDFs are in the selected PDF folder.

### "Invalid file" error

- Make sure your input file is a valid CSV or Excel file (.csv, .xlsx, or .xls).
- Ensure the file has a column named `serial_numbers`.

### Application won't start

- Make sure you have a valid license file (`license.json`) in the application folder.
- Contact support if the problem persists.

## Output Files

- Each row in your input file produces one merged PDF.
- Files are named: `merged_row_1.pdf`, `merged_row_2.pdf`, etc.
- If a row has no matching PDFs, no file is created for that row (check the log for details).

## Support

For technical support or license issues, please contact your software provider.

---

**Version**: 1.0.0
