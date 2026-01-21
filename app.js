// PDF Merger Application Logic

class PDFMergerApp {
    constructor() {
        this.dataFile = null;
        this.pdfFiles = new Map(); // Map of filename -> File object
        this.outputFolder = null;
        this.isProcessing = false;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Data file selection
        document.getElementById('chooseDataFileBtn').addEventListener('click', () => {
            document.getElementById('dataFile').click();
        });
        document.getElementById('dataFile').addEventListener('change', (e) => {
            this.handleDataFileSelect(e.target.files[0]);
        });

        // PDF folder selection
        document.getElementById('choosePdfFolderBtn').addEventListener('click', () => {
            document.getElementById('pdfFolder').click();
        });
        document.getElementById('pdfFolder').addEventListener('change', (e) => {
            this.handlePdfFolderSelect(e.target.files);
        });

        // Output folder - browser limitation (files download to default download folder)
        // No action needed, input is pre-filled and button is hidden

        // Mode toggle
        document.querySelectorAll('.segment').forEach(segment => {
            segment.addEventListener('click', () => {
                document.querySelectorAll('.segment').forEach(s => s.classList.remove('active'));
                segment.classList.add('active');
            });
        });

        // Run merge button
        document.getElementById('runMergeBtn').addEventListener('click', () => {
            this.runMerge();
        });
    }

    handleDataFileSelect(file) {
        if (!file) return;
        
        this.dataFile = file;
        document.getElementById('dataFileInput').value = file.name;
        this.addLog('success', `Data file selected: ${file.name}`);
    }

    handlePdfFolderSelect(files) {
        if (!files || files.length === 0) return;

        // Filter only PDF files
        const pdfFiles = Array.from(files).filter(f => 
            f.name.toLowerCase().endsWith('.pdf')
        );

        // Build map: filename (without extension) -> File object
        this.pdfFiles.clear();
        pdfFiles.forEach(file => {
            const nameWithoutExt = file.name.replace(/\.pdf$/i, '');
            // Store both with and without extension for matching
            this.pdfFiles.set(nameWithoutExt.toLowerCase(), file);
            this.pdfFiles.set(file.name.toLowerCase(), file);
        });

        document.getElementById('pdfFolderInput').value = `${pdfFiles.length} PDF file(s) selected`;
        this.addLog('success', `Found ${pdfFiles.length} PDF file(s)`);
    }

    async parseDataFile() {
        if (!this.dataFile) {
            throw new Error('No data file selected');
        }

        const fileName = this.dataFile.name.toLowerCase();
        let rows = [];

        if (fileName.endsWith('.csv')) {
            rows = await this.parseCSV(this.dataFile);
        } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
            rows = await this.parseExcel(this.dataFile);
        } else {
            throw new Error('Unsupported file format. Please use CSV or Excel files.');
        }

        // Validate that serial_numbers column exists
        if (rows.length === 0) {
            throw new Error('Data file is empty');
        }

        const firstRow = rows[0];
        if (!('serial_numbers' in firstRow)) {
            const availableColumns = Object.keys(firstRow).join(', ');
            throw new Error(`Column 'serial_numbers' not found. Available columns: ${availableColumns}`);
        }

        return rows;
    }

    parseCSV(file) {
        return new Promise((resolve, reject) => {
            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                complete: (results) => {
                    if (results.errors.length > 0) {
                        reject(new Error(`CSV parsing error: ${results.errors[0].message}`));
                    } else {
                        resolve(results.data);
                    }
                },
                error: (error) => {
                    reject(new Error(`Failed to parse CSV: ${error.message}`));
                }
            });
        });
    }

    async parseExcel(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    const firstSheetName = workbook.SheetNames[0];
                    const worksheet = workbook.Sheets[firstSheetName];
                    const jsonData = XLSX.utils.sheet_to_json(worksheet);
                    resolve(jsonData);
                } catch (error) {
                    reject(new Error(`Failed to parse Excel file: ${error.message}`));
                }
            };
            reader.onerror = () => {
                reject(new Error('Failed to read Excel file'));
            };
            reader.readAsArrayBuffer(file);
        });
    }

    findPdfFile(filename) {
        // Try exact match (case-insensitive)
        const lowerFilename = filename.toLowerCase();
        
        // Try with .pdf extension
        if (this.pdfFiles.has(lowerFilename + '.pdf')) {
            return this.pdfFiles.get(lowerFilename + '.pdf');
        }
        
        // Try without extension
        if (this.pdfFiles.has(lowerFilename)) {
            return this.pdfFiles.get(lowerFilename);
        }

        // Try removing .pdf if present
        const withoutExt = lowerFilename.replace(/\.pdf$/, '');
        if (this.pdfFiles.has(withoutExt)) {
            return this.pdfFiles.get(withoutExt);
        }

        // Fuzzy matching (if enabled)
        const fuzzyMatching = document.getElementById('fuzzyMatching').checked;
        if (fuzzyMatching) {
            // Find closest match
            for (const [key, file] of this.pdfFiles.entries()) {
                if (key.includes(withoutExt) || withoutExt.includes(key)) {
                    return file;
                }
            }
        }

        return null;
    }

    async mergePdfs(pdfFiles, outputName) {
        try {
            const { PDFDocument } = PDFLib;
            const mergedPdf = await PDFDocument.create();

            for (const pdfFile of pdfFiles) {
                const arrayBuffer = await pdfFile.arrayBuffer();
                const pdf = await PDFDocument.load(arrayBuffer);
                const pages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
                pages.forEach((page) => mergedPdf.addPage(page));
            }

            const pdfBytes = await mergedPdf.save();
            return pdfBytes;
        } catch (error) {
            throw new Error(`Failed to merge PDFs: ${error.message}`);
        }
    }

    parseSerialNumbers(serialNumbersStr) {
        if (!serialNumbersStr || !serialNumbersStr.trim()) {
            return [];
        }
        return serialNumbersStr.split(',')
            .map(s => s.trim())
            .filter(s => s.length > 0);
    }

    async processRow(rowIndex, serialNumbersStr, filenamePattern) {
        const filenames = this.parseSerialNumbers(serialNumbersStr);
        
        if (filenames.length === 0) {
            this.addLog('warning', `Row ${rowIndex + 1}: No filenames found, skipping...`);
            return { success: false, skipped: true };
        }

        this.addLog('success', `Row ${rowIndex + 1}: Processing filenames: ${filenames.join(', ')}`);

        // Find PDF files
        const pdfFiles = [];
        const missingFiles = [];

        for (const filename of filenames) {
            const pdfFile = this.findPdfFile(filename);
            if (pdfFile) {
                pdfFiles.push(pdfFile);
                this.addLog('success', `  Found: ${pdfFile.name}`);
            } else {
                missingFiles.push(filename);
                this.addLog('warning', `  PDF file not found for filename '${filename}'`);
            }
        }

        if (pdfFiles.length === 0) {
            this.addLog('warning', `Row ${rowIndex + 1}: No PDF files found for any filenames, skipping...`);
            return { success: false, skipped: true };
        }

            // Generate output filename
            // Support both {index} and {row_name} patterns
            let outputFilename = filenamePattern.replace(/\{index\}/g, rowIndex + 1);
            // For {row_name}, use first filename or row number as fallback
            const rowName = filenames[0] || `row_${rowIndex + 1}`;
            outputFilename = outputFilename.replace(/\{row_name\}/g, rowName);
            
            // Ensure .pdf extension
            if (!outputFilename.toLowerCase().endsWith('.pdf')) {
                outputFilename += '.pdf';
            }

        // Merge PDFs
        try {
            this.addLog('success', `  Merging ${pdfFiles.length} PDF(s) into ${outputFilename}...`);
            const pdfBytes = await this.mergePdfs(pdfFiles, outputFilename);
            
            // Download the merged PDF
            this.downloadFile(pdfBytes, outputFilename);
            
            this.addLog('success', `  ✓ Successfully created ${outputFilename}`);
            return { success: true, skipped: false };
        } catch (error) {
            this.addLog('error', `  ✗ Failed to create ${outputFilename}: ${error.message}`);
            return { success: false, skipped: false };
        }
    }

    downloadFile(data, filename) {
        const blob = new Blob([data], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async runMerge() {
        if (this.isProcessing) {
            return;
        }

        // Validate inputs
        if (!this.dataFile) {
            alert('Please select a data file (CSV or Excel)');
            return;
        }

        if (this.pdfFiles.size === 0) {
            alert('Please select a folder containing PDF files');
            return;
        }

        this.isProcessing = true;
        document.getElementById('runMergeBtn').disabled = true;

        // Show processing section
        document.getElementById('processingSection').style.display = 'block';
        document.getElementById('summaryPanel').style.display = 'block';
        
        // Reset UI
        document.getElementById('logPanel').innerHTML = '';
        document.getElementById('progressFill').style.width = '0%';
        this.updateSummary(0, 0, 0);

        let successCount = 0;
        let failedCount = 0;
        let skippedCount = 0;

        try {
            // Parse data file
            this.addLog('success', 'Parsing data file...');
            const rows = await this.parseDataFile();
            const totalRows = rows.length;
            
            this.addLog('success', `Found ${totalRows} row(s) to process`);

            // Get filename pattern
            const filenamePattern = document.getElementById('filenamePattern').value || 'merged_row_{index}.pdf';

            // Process each row
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const serialNumbers = row.serial_numbers || '';

                const result = await this.processRow(i, serialNumbers, filenamePattern);

                if (result.success) {
                    successCount++;
                } else if (result.skipped) {
                    skippedCount++;
                } else {
                    failedCount++;
                }

                // Update progress
                const progress = ((i + 1) / totalRows) * 100;
                document.getElementById('progressFill').style.width = `${progress}%`;
                document.getElementById('progressText').textContent = 
                    `Merging PDFs… ${i + 1} of ${totalRows} completed`;

                // Update summary
                this.updateSummary(successCount, failedCount, skippedCount);

                // Small delay for UI responsiveness
                await new Promise(resolve => setTimeout(resolve, 50));
            }

            this.addLog('success', `\nProcessing complete!`);
            this.addLog('success', `Total rows processed: ${totalRows}`);
            this.addLog('success', `Successfully merged: ${successCount}`);
            if (failedCount > 0) {
                this.addLog('error', `Failed: ${failedCount}`);
            }
            if (skippedCount > 0) {
                this.addLog('warning', `Skipped: ${skippedCount}`);
            }

        } catch (error) {
            this.addLog('error', `Error: ${error.message}`);
            alert(`Error: ${error.message}`);
        } finally {
            this.isProcessing = false;
            document.getElementById('runMergeBtn').disabled = false;
        }
    }

    addLog(type, message) {
        const logPanel = document.getElementById('logPanel');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = message;
        logPanel.appendChild(entry);
        logPanel.scrollTop = logPanel.scrollHeight;
    }

    updateSummary(success, failed, skipped) {
        document.getElementById('successCount').textContent = success;
        document.getElementById('failedCount').textContent = failed;
        document.getElementById('skippedCount').textContent = skipped;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PDFMergerApp();
});
