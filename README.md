# PDF Merger from CSV Serial Numbers

This script merges PDF files based on serial numbers specified in a CSV file. Each row in the CSV produces one merged PDF document.

## Requirements

- Python 3.6 or higher
- pypdf library

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with the following command:

```bash
python merge_pdfs.py --csv <csv_file> --folder <pdf_folder> --output <output_folder>
```

### Arguments

- `--csv`: Path to the CSV file containing the `serial_numbers` column
- `--folder`: Path to the folder containing the PDF files to merge
- `--output`: Path to the output folder where merged PDFs will be saved

### Example

```bash
python merge_pdfs.py --csv data.csv --folder ./pdfs --output ./merged_output
```

## CSV Format

The CSV file must contain a column named `serial_numbers`. Each row should contain comma-separated filenames (strings) that correspond to PDF files in your folder.

### Example CSV

```csv
serial_numbers
ABC123,DEF456,GHI789
ABC123,XYZ999
document1,document2,document3
```

This will create:
- `merged_row_1.pdf` - merges ABC123.pdf, DEF456.pdf, GHI789.pdf
- `merged_row_2.pdf` - merges ABC123.pdf, XYZ999.pdf
- `merged_row_3.pdf` - merges document1.pdf, document2.pdf, document3.pdf

## PDF File Naming

The script looks for PDF files matching the filenames specified in the CSV. Each string in the `serial_numbers` column represents a unique filename. The script will:
- Look for files with the exact filename (with or without `.pdf` extension)
- Try case-insensitive matching if exact match is not found

For example:
- Filename `ABC123` → looks for `ABC123.pdf` or `ABC123`
- Filename `document1.pdf` → looks for `document1.pdf`
- Filename `MyFile` → looks for `MyFile.pdf` or `MyFile`

## Output

Merged PDFs are saved in the output folder with names like:
- `merged_row_1.pdf`
- `merged_row_2.pdf`
- `merged_row_3.pdf`
- etc.

The script will display progress information and a summary when complete.
