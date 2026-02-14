"""File and extension constants for PDF Merger."""


class FileConstants:
    """File extensions and output naming."""
    EXCEL_FILE_EXTENSIONS = {'.xlsx', '.xls'}
    CSV_FILE_EXTENSIONS = {'.csv'}
    PDF_FILE_EXTENSIONS = {'.pdf'}
    PDF_FILE_EXTENSION = '.pdf'
    SOURCE_FILE_EXTENSIONS = PDF_FILE_EXTENSIONS | EXCEL_FILE_EXTENSIONS  # type: ignore
    OUTPUT_FILENAME_PATTERN = 'merged_row_{}.pdf'
