"""
Operations module.
File-format operations: PDF merge, streaming PDF, Excel-to-PDF conversion.
(Workflow and data orchestration live in core/.)

Public surface: find_source_file, merge_pdfs (pdf_merger.py); convert_excel_to_pdf
(excel_to_pdf_converter.py); merge_pdfs_streaming, should_use_streaming
(streaming_pdf_merger.py). Internal helpers (e.g. _get_pdf_libraries,
suppress_stderr) are private; do not depend on them from outside this package.
"""
