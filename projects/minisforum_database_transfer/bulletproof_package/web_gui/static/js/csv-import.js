// ==================== CSV Import Functionality ====================

// Add CSV import methods to the MinisFornumApp prototype
MinisFornumApp.prototype.initializeCSVImport = function() {
    console.log('Initializing CSV import functionality...');
    
    const csvFileInput = document.getElementById('csvFileInput');
    const uploadDropzone = document.getElementById('uploadDropzone');
    const csvInfo = document.getElementById('csvInfo');
    const csvDealershipSelect = document.getElementById('csvDealershipSelect');
    const processCSVBtn = document.getElementById('processCSVBtn');
    const clearCSVBtn = document.getElementById('clearCSVBtn');
    
    // Populate dealership dropdown
    this.populateCSVDealershipSelect();
    
    // File input change handler
    if (csvFileInput) {
        csvFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleCSVFileSelect(file);
            }
        });
    }
    
    // Drag and drop handlers
    if (uploadDropzone) {
        uploadDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadDropzone.classList.add('drag-over');
        });
        
        uploadDropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadDropzone.classList.remove('drag-over');
        });
        
        uploadDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadDropzone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === 'text/csv') {
                this.handleCSVFileSelect(files[0]);
            } else {
                alert('Please drop a valid CSV file.');
            }
        });
    }
    
    // Dealership selection change
    if (csvDealershipSelect) {
        csvDealershipSelect.addEventListener('change', () => {
            this.updateProcessButton();
        });
    }
    
    // Process CSV button
    if (processCSVBtn) {
        processCSVBtn.addEventListener('click', () => {
            this.processCSVImport();
        });
    }
    
    // Clear CSV button
    if (clearCSVBtn) {
        clearCSVBtn.addEventListener('click', () => {
            this.clearCSVImport();
        });
    }
};

MinisFornumApp.prototype.populateCSVDealershipSelect = function() {
    const select = document.getElementById('csvDealershipSelect');
    if (!select || !this.dealerships) return;
    
    // Clear existing options except the first one
    select.innerHTML = '<option value="">Choose dealership...</option>';
    
    // Add dealership options
    this.dealerships.forEach(dealership => {
        const option = document.createElement('option');
        option.value = dealership.name;
        option.textContent = dealership.name;
        select.appendChild(option);
    });
};

MinisFornumApp.prototype.handleCSVFileSelect = function(file) {
    console.log('CSV file selected:', file.name);
    
    // Store the selected file
    this.selectedCSVFile = file;
    
    // Update UI
    const fileName = document.getElementById('fileName');
    const fileDetails = document.getElementById('fileDetails');
    const csvInfo = document.getElementById('csvInfo');
    const uploadDropzone = document.getElementById('uploadDropzone');
    
    if (fileName) fileName.textContent = file.name;
    if (fileDetails) {
        const sizeKB = Math.round(file.size / 1024);
        fileDetails.textContent = `Size: ${sizeKB} KB • Type: ${file.type || 'CSV'}`;
    }
    
    // Show CSV info panel and hide upload zone
    if (csvInfo) csvInfo.style.display = 'block';
    if (uploadDropzone) uploadDropzone.style.display = 'none';
    
    // Update process button state
    this.updateProcessButton();
    
    // Preview CSV content
    this.previewCSVContent(file);
};

MinisFornumApp.prototype.previewCSVContent = function(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const csvText = e.target.result;
            const lines = csvText.split('\\n').filter(line => line.trim());
            
            if (lines.length > 0) {
                const headers = lines[0].split(',').map(h => h.trim().replace(/\"/g, ''));
                const dataRows = lines.length - 1;
                
                console.log('CSV Preview:', {
                    headers: headers,
                    totalRows: dataRows,
                    sampleData: lines.slice(0, 3)
                });
                
                // Update file details with row count
                const fileDetails = document.getElementById('fileDetails');
                if (fileDetails) {
                    const sizeKB = Math.round(file.size / 1024);
                    fileDetails.textContent = `Size: ${sizeKB} KB • Rows: ${dataRows} • Columns: ${headers.length}`;
                }
            }
        } catch (error) {
            console.error('Error previewing CSV:', error);
        }
    };
    reader.readAsText(file);
};

MinisFornumApp.prototype.updateProcessButton = function() {
    const processBtn = document.getElementById('processCSVBtn');
    const dealershipSelect = document.getElementById('csvDealershipSelect');
    
    if (processBtn && dealershipSelect) {
        const canProcess = this.selectedCSVFile && dealershipSelect.value;
        processBtn.disabled = !canProcess;
    }
};

MinisFornumApp.prototype.processCSVImport = async function() {
    if (!this.selectedCSVFile) {
        alert('No CSV file selected');
        return;
    }
    
    const dealershipSelect = document.getElementById('csvDealershipSelect');
    const orderTypeSelect = document.getElementById('csvOrderType');
    const processBtn = document.getElementById('processCSVBtn');
    
    if (!dealershipSelect.value) {
        alert('Please select a dealership');
        return;
    }
    
    // Disable button and show processing state
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Processing...';
    
    try {
        // Create form data
        const formData = new FormData();
        const keepDataCheckbox = document.getElementById('keepDataForWizard');
        
        formData.append('csv_file', this.selectedCSVFile);
        formData.append('dealership', dealershipSelect.value);
        formData.append('order_type', orderTypeSelect.value);
        formData.append('keep_data', keepDataCheckbox.checked ? 'true' : 'false');
        
        console.log('Processing CSV import...', {
            file: this.selectedCSVFile.name,
            dealership: dealershipSelect.value,
            orderType: orderTypeSelect.value
        });
        
        // Send to server
        const response = await fetch('/api/csv-import/process', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success results
            this.showCSVProcessingResults(result);
        } else {
            throw new Error(result.error || 'Processing failed');
        }
        
    } catch (error) {
        console.error('Error processing CSV:', error);
        alert(`CSV processing failed: ${error.message}`);
    } finally {
        // Restore button
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class=\"fas fa-cogs\"></i> Process CSV Order';
    }
};

MinisFornumApp.prototype.showCSVProcessingResults = function(result) {
    const csvInfo = result.csv_import_info;
    
    // Create results modal or update UI with results
    let message = `CSV Import Processing Complete!\\n\\n`;
    message += `File: ${csvInfo.filename}\\n`;
    message += `Dealership: ${csvInfo.dealership}\\n`;
    message += `Order Type: ${csvInfo.order_type.toUpperCase()}\\n`;
    message += `Total CSV Rows: ${csvInfo.total_rows}\\n`;
    
    // Add CSV-specific validation info
    if (result.csv_vehicles_imported !== undefined) {
        message += `Vehicles Imported: ${result.csv_vehicles_imported}\\n`;
        message += `Vehicles Skipped: ${result.csv_vehicles_skipped || 0}\\n`;
        if (result.csv_filtering_applied) {
            message += `Applied Filters: ${result.csv_filtering_applied.join(', ')}\\n`;
        }
    }
    message += `\\n`;
    
    if (result.success) {
        message += `ORDER PROCESSING RESULTS:\\n`;
        message += `• Vehicles Processed: ${result.vehicles_processed || result.new_vehicles || 0}\\n`;
        message += `• QR Codes Generated: ${result.qr_codes_generated || 0}\\n`;
        message += `• VINs Logged to History: ${result.vins_logged_to_history || 0}\\n`;
        
        if (result.csv_file) {
            message += `\\nOutput Files:\\n`;
            message += `• CSV File: ${result.csv_file}\\n`;
            message += `• QR Folder: ${result.qr_folder}\\n`;
        }
        
        message += `\\nValidation Complete! Compare these results with your Google Sheets method.`;
        
        if (result.data_kept_for_wizard) {
            message += `\\n\\nDATA KEPT FOR WIZARD TESTING`;
            message += `\\nImport timestamp: ${result.import_timestamp}`;
            message += `\\nYou can now use the Order Processing Wizard to test with this imported data.`;
            message += `\\nThe data is marked as 'CSV_TEST_IMPORT' for easy identification.`;
        }
    } else {
        message += `ERROR: ${result.error}\\n`;
        message += `The CSV was imported but order processing failed. Check logs for details.`;
    }
    
    alert(message);
    
    console.log('CSV Processing Results:', result);
};

MinisFornumApp.prototype.clearCSVImport = function() {
    // Reset file input
    const csvFileInput = document.getElementById('csvFileInput');
    if (csvFileInput) csvFileInput.value = '';
    
    // Clear stored file
    this.selectedCSVFile = null;
    
    // Reset UI
    const csvInfo = document.getElementById('csvInfo');
    const uploadDropzone = document.getElementById('uploadDropzone');
    const dealershipSelect = document.getElementById('csvDealershipSelect');
    const orderTypeSelect = document.getElementById('csvOrderType');
    
    if (csvInfo) csvInfo.style.display = 'none';
    if (uploadDropzone) uploadDropzone.style.display = 'block';
    if (dealershipSelect) dealershipSelect.value = '';
    if (orderTypeSelect) orderTypeSelect.value = 'cao';
    
    // Update process button
    this.updateProcessButton();
};

// Initialize CSV import when queue management tab is clicked
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const queueTab = document.querySelector('[data-tab=\"queue-management\"]');
        if (queueTab && typeof app !== 'undefined') {
            queueTab.addEventListener('click', () => {
                // Initialize CSV import if not already done
                if (!app.csvImportInitialized) {
                    app.initializeCSVImport();
                    app.csvImportInitialized = true;
                }
            });
        }
    }, 500);
});