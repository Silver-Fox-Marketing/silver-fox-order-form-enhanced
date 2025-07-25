/**
 * MinisForum Database Web GUI - JavaScript Application
 * Silver Fox Marketing - Dealership Management Interface
 * 
 * Handles all frontend interactions, API calls, and real-time updates
 * for the dealership database control system.
 */

class MinisFornumApp {
    constructor() {
        this.dealerships = [];
        this.selectedDealerships = new Set();
        this.scraperRunning = false;
        this.currentTab = 'scraper';
        this.currentDealership = null;
        
        // Initialize the application
        this.init();
    }
    
    init() {
        console.log('Initializing MinisForum Database GUI...');
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Load initial data
        this.loadDealerships();
        this.checkScraperStatus();
        
        // Set up periodic status checks
        this.startStatusPolling();
        
        console.log('Application initialized successfully');
    }
    
    bindEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Main action buttons
        document.getElementById('startScrapeBtn').addEventListener('click', () => {
            this.startScraper();
        });
        
        document.getElementById('scheduleBtn').addEventListener('click', () => {
            this.showScheduleModal();
        });
        
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal('dealershipModal');
        });
        
        document.getElementById('closeScheduleModal').addEventListener('click', () => {
            this.closeModal('scheduleModal');
        });
        
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveDealershipSettings();
        });
        
        document.getElementById('saveSchedule').addEventListener('click', () => {
            this.saveScheduleSettings();
        });
        
        // Terminal controls
        document.getElementById('clearTerminal').addEventListener('click', () => {
            this.clearTerminal();
        });
        
        // Report generation buttons
        document.getElementById('generateAdobeBtn').addEventListener('click', () => {
            this.generateAdobeReport();
        });
        
        document.getElementById('generateSummaryBtn').addEventListener('click', () => {
            this.generateSummaryReport();
        });
        
        // Refresh buttons for data tabs
        document.getElementById('refreshRawData').addEventListener('click', () => {
            this.loadRawDataOverview();
        });
        
        document.getElementById('refreshNormalizedData').addEventListener('click', () => {
            this.loadNormalizedDataOverview();
        });
        
        document.getElementById('refreshOrderData').addEventListener('click', () => {
            this.loadOrderProcessingOverview();
        });
        
        document.getElementById('refreshQRData').addEventListener('click', () => {
            this.loadQROverview();
        });
        
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }
    
    async loadDealerships() {
        try {
            this.addTerminalMessage('Loading dealership configurations...', 'info');
            
            const response = await fetch('/api/dealerships');
            const dealerships = await response.json();
            
            this.dealerships = dealerships;
            this.renderDealershipGrid();
            
            // Select all active dealerships by default
            this.dealerships.forEach(dealership => {
                if (dealership.is_active) {
                    this.selectedDealerships.add(dealership.name);
                }
            });
            
            this.updateDealershipSelection();
            this.addTerminalMessage(`Loaded ${dealerships.length} dealership configurations`, 'success');
            
        } catch (error) {
            console.error('Error loading dealerships:', error);
            this.addTerminalMessage(`Error loading dealerships: ${error.message}`, 'error');
        }
    }
    
    renderDealershipGrid() {
        const grid = document.getElementById('dealershipGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        this.dealerships.forEach(dealership => {
            const card = this.createDealershipCard(dealership);
            grid.appendChild(card);
        });
    }
    
    createDealershipCard(dealership) {
        const card = document.createElement('div');
        card.className = `dealership-card ${dealership.is_active ? 'active' : 'inactive'}`;
        card.dataset.dealership = dealership.name;
        
        // Get filtering rules for display
        const filteringRules = dealership.filtering_rules || {};
        const vehicleTypes = this.getEnabledVehicleTypes(filteringRules);
        const priceRange = this.getPriceRange(filteringRules);
        
        card.innerHTML = `
            <div class="card-header">
                <input type="checkbox" class="dealership-checkbox" 
                       ${this.selectedDealerships.has(dealership.name) ? 'checked' : ''}
                       onchange="app.toggleDealershipSelection('${dealership.name}', this.checked)">
                <h3 class="dealership-name">${dealership.name}</h3>
                <button class="settings-btn" onclick="app.showDealershipSettings('${dealership.name}')">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
            <div class="dealership-info">
                <div class="info-row">
                    <span class="info-label">Vehicle Types:</span>
                    <span class="info-value">${vehicleTypes}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Price Range:</span>
                    <span class="info-value">${priceRange}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value ${dealership.is_active ? 'success' : 'error'}">
                        ${dealership.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    getEnabledVehicleTypes(filteringRules) {
        const excludeConditions = filteringRules.exclude_conditions || [];
        const types = [];
        
        if (!excludeConditions.includes('new')) types.push('New');
        if (!excludeConditions.includes('po')) types.push('Pre-Owned');
        if (!excludeConditions.includes('cpo')) types.push('CPO');
        
        return types.length > 0 ? types.join(', ') : 'None';
    }
    
    getPriceRange(filteringRules) {
        const minPrice = filteringRules.min_price;
        const maxPrice = filteringRules.max_price;
        
        if (minPrice && maxPrice) {
            return `$${minPrice.toLocaleString()} - $${maxPrice.toLocaleString()}`;
        } else if (minPrice) {
            return `$${minPrice.toLocaleString()}+`;
        } else if (maxPrice) {
            return `Up to $${maxPrice.toLocaleString()}`;
        } else {
            return 'Any Price';
        }
    }
    
    toggleDealershipSelection(dealershipName, selected) {
        if (selected) {
            this.selectedDealerships.add(dealershipName);
        } else {
            this.selectedDealerships.delete(dealershipName);
        }
        
        this.updateDealershipSelection();
        this.addTerminalMessage(`${dealershipName} ${selected ? 'selected' : 'deselected'} for scraping`, 'info');
    }
    
    updateDealershipSelection() {
        // Update visual selection state
        document.querySelectorAll('.dealership-card').forEach(card => {
            const dealershipName = card.dataset.dealership;
            const isSelected = this.selectedDealerships.has(dealershipName);
            
            card.classList.toggle('selected', isSelected);
            
            const checkbox = card.querySelector('.dealership-checkbox');
            if (checkbox) {
                checkbox.checked = isSelected;
            }
        });
        
        // Update start button state
        const startButton = document.getElementById('startScrapeBtn');
        if (startButton) {
            startButton.disabled = this.selectedDealerships.size === 0 || this.scraperRunning;
            
            const buttonText = startButton.querySelector('span') || startButton;
            if (this.scraperRunning) {
                buttonText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            } else {
                buttonText.innerHTML = '<i class="fas fa-play"></i> Start Scrape';
            }
        }
    }
    
    showDealershipSettings(dealershipName) {
        this.currentDealership = dealershipName;
        const dealership = this.dealerships.find(d => d.name === dealershipName);
        
        if (!dealership) return;
        
        // Populate modal with current settings
        document.getElementById('modalTitle').textContent = `${dealershipName} Settings`;
        
        const filteringRules = dealership.filtering_rules || {};
        const excludeConditions = filteringRules.exclude_conditions || [];
        
        // Set vehicle type checkboxes
        document.querySelector('input[value="new"]').checked = !excludeConditions.includes('new');
        document.querySelector('input[value="po"]').checked = !excludeConditions.includes('po');
        document.querySelector('input[value="cpo"]').checked = !excludeConditions.includes('cpo');
        
        // Set price and year filters
        document.getElementById('minPrice').value = filteringRules.min_price || '';
        document.getElementById('maxPrice').value = filteringRules.max_price || '';
        document.getElementById('minYear').value = filteringRules.min_year || '';
        
        this.showModal('dealershipModal');
    }
    
    async saveDealershipSettings() {
        if (!this.currentDealership) return;
        
        try {
            // Collect form data
            const vehicleTypes = Array.from(document.querySelectorAll('input[name="vehicle_types"]:checked'))
                .map(input => input.value);
            
            const excludeConditions = ['new', 'po', 'cpo'].filter(type => !vehicleTypes.includes(type));
            
            const filteringRules = {
                exclude_conditions: excludeConditions,
                require_stock: true
            };
            
            // Add price filters if specified
            const minPrice = parseInt(document.getElementById('minPrice').value);
            const maxPrice = parseInt(document.getElementById('maxPrice').value);
            const minYear = parseInt(document.getElementById('minYear').value);
            
            if (minPrice) filteringRules.min_price = minPrice;
            if (maxPrice) filteringRules.max_price = maxPrice;
            if (minYear) filteringRules.min_year = minYear;
            
            // Send update to server
            const response = await fetch(`/api/dealerships/${this.currentDealership}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filtering_rules: filteringRules,
                    is_active: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Updated settings for ${this.currentDealership}`, 'success');
                this.closeModal('dealershipModal');
                this.loadDealerships(); // Refresh the grid
            } else {
                this.addTerminalMessage(`Failed to update ${this.currentDealership}: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Error saving dealership settings:', error);
            this.addTerminalMessage(`Error saving settings: ${error.message}`, 'error');
        }
    }
    
    async startScraper() {
        if (this.scraperRunning || this.selectedDealerships.size === 0) return;
        
        try {
            this.scraperRunning = true;
            this.updateDealershipSelection();
            
            this.addTerminalMessage('Starting scraper pipeline...', 'info');
            this.showScraperStatus();
            
            const response = await fetch('/api/scraper/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dealerships: Array.from(this.selectedDealerships)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage('Scraper started successfully', 'success');
            } else {
                this.addTerminalMessage(`Failed to start scraper: ${result.message}`, 'error');
                this.scraperRunning = false;
                this.updateDealershipSelection();
                this.hideScraperStatus();
            }
            
        } catch (error) {
            console.error('Error starting scraper:', error);
            this.addTerminalMessage(`Error starting scraper: ${error.message}`, 'error');
            this.scraperRunning = false;
            this.updateDealershipSelection();
            this.hideScraperStatus();
        }
    }
    
    async checkScraperStatus() {
        try {
            const response = await fetch('/api/scraper/status');
            const status = await response.json();
            
            this.scraperRunning = status.running;
            
            if (status.last_scrape) {
                const lastScrape = new Date(status.last_scrape);
                document.getElementById('lastScrape').textContent = 
                    `Last Scrape: ${lastScrape.toLocaleDateString()} ${lastScrape.toLocaleTimeString()}`;
            }
            
            if (status.results && Object.keys(status.results).length > 0) {
                this.updateScraperProgress(status.results);
            }
            
            this.updateDealershipSelection();
            
            // Update system status
            const statusIndicator = document.getElementById('systemStatus');
            const statusIcon = statusIndicator.querySelector('.status-icon');
            const statusText = statusIndicator.querySelector('.status-text');
            
            if (this.scraperRunning) {
                statusIcon.className = 'fas fa-circle status-icon warning';
                statusText.textContent = 'Scraper Running';
            } else {
                statusIcon.className = 'fas fa-circle status-icon';
                statusText.textContent = 'System Ready';
            }
            
        } catch (error) {
            console.error('Error checking scraper status:', error);
        }
    }
    
    updateScraperProgress(results) {
        const statusElement = document.getElementById('scraperStatus');
        const progressFill = document.getElementById('progressFill');
        const statusDetails = document.getElementById('statusDetails');
        
        if (!results.dealerships) return;
        
        const totalDealerships = Object.keys(results.dealerships).length;
        const completedDealerships = Object.values(results.dealerships)
            .filter(d => d.status === 'completed' || d.status === 'failed').length;
        
        const progress = totalDealerships > 0 ? (completedDealerships / totalDealerships) * 100 : 0;
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (statusDetails) {
            const totalVehicles = Object.values(results.dealerships)
                .reduce((sum, d) => sum + (d.vehicle_count || 0), 0);
            
            statusDetails.innerHTML = `
                <div class="status-item">
                    <span class="status-number">${completedDealerships}</span>
                    <span class="status-label">Dealerships Processed</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${totalVehicles}</span>
                    <span class="status-label">Vehicles Processed</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${results.errors ? results.errors.length : 0}</span>
                    <span class="status-label">Errors</span>
                </div>
                <div class="status-item">
                    <span class="status-number">${Math.round(progress)}%</span>
                    <span class="status-label">Complete</span>
                </div>
            `;
        }
        
        // Hide status when complete
        if (progress >= 100 && !this.scraperRunning) {
            setTimeout(() => {
                this.hideScraperStatus();
            }, 3000);
        }
    }
    
    showScraperStatus() {
        const statusElement = document.getElementById('scraperStatus');
        if (statusElement) {
            statusElement.style.display = 'block';
        }
    }
    
    hideScraperStatus() {
        const statusElement = document.getElementById('scraperStatus');
        if (statusElement) {
            statusElement.style.display = 'none';
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-panel`).classList.add('active');
        
        this.currentTab = tabName;
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }
    
    loadTabData(tabName) {
        switch (tabName) {
            case 'raw-data':
                this.loadRawDataOverview();
                break;
            case 'normalized-data':
                this.loadNormalizedDataOverview();
                break;
            case 'order-processing':
                this.loadOrderProcessingOverview();
                break;
            case 'qr-generation':
                this.loadQROverview();
                break;
            case 'adobe-export':
                this.loadExportFiles();
                break;
        }
    }
    
    async loadRawDataOverview() {
        // This would load raw data statistics
        const overview = document.getElementById('rawDataOverview');
        if (overview) {
            overview.innerHTML = `
                <div class="overview-card">
                    <h3>Import Statistics</h3>
                    <div class="metric">
                        <span class="metric-label">Total Records</span>
                        <span class="metric-value">Loading...</span>
                    </div>
                </div>
            `;
        }
    }
    
    async loadNormalizedDataOverview() {
        // This would load normalized data statistics
        const overview = document.getElementById('normalizedDataOverview');
        if (overview) {
            overview.innerHTML = `
                <div class="overview-card">
                    <h3>Normalized Data</h3>
                    <div class="metric">
                        <span class="metric-label">Processed Vehicles</span>
                        <span class="metric-value">Loading...</span>
                    </div>
                </div>
            `;
        }
    }
    
    async loadOrderProcessingOverview() {
        // This would load order processing statistics
        const overview = document.getElementById('orderStatusOverview');
        if (overview) {
            overview.innerHTML = `
                <div class="overview-card">
                    <h3>Order Processing</h3>
                    <div class="metric">
                        <span class="metric-label">Active Jobs</span>
                        <span class="metric-value">Loading...</span>
                    </div>
                </div>
            `;
        }
    }
    
    async loadQROverview() {
        // This would load QR generation statistics
        const overview = document.getElementById('qrOverview');
        if (overview) {
            overview.innerHTML = `
                <div class="overview-card">
                    <h3>QR Generation</h3>
                    <div class="metric">
                        <span class="metric-label">QR Codes Generated</span>
                        <span class="metric-value">Loading...</span>
                    </div>
                </div>
            `;
        }
    }
    
    async loadExportFiles() {
        // This would load available export files
        const exportFiles = document.getElementById('exportFiles');
        if (exportFiles) {
            exportFiles.innerHTML = `
                <div class="export-file">
                    <div class="file-info">
                        <div class="file-name">No export files available</div>
                        <div class="file-details">Run a scrape to generate export files</div>
                    </div>
                </div>
            `;
        }
    }
    
    async generateAdobeReport() {
        try {
            this.addTerminalMessage('Generating Adobe export files...', 'info');
            
            const selectedDealerships = Array.from(this.selectedDealerships);
            const queryParams = selectedDealerships.map(d => `dealerships=${encodeURIComponent(d)}`).join('&');
            
            const response = await fetch(`/api/reports/adobe?${queryParams}`);
            const result = await response.json();
            
            if (result.success) {
                this.addTerminalMessage(`Generated ${result.count} Adobe export files`, 'success');
                this.loadExportFiles(); // Refresh the export files list
            } else {
                this.addTerminalMessage('Failed to generate Adobe export files', 'error');
            }
            
        } catch (error) {
            console.error('Error generating Adobe report:', error);
            this.addTerminalMessage(`Error generating Adobe report: ${error.message}`, 'error');
        }
    }
    
    async generateSummaryReport() {
        try {
            this.addTerminalMessage('Generating summary report...', 'info');
            
            const response = await fetch('/api/reports/summary');
            const report = await response.json();
            
            if (report.error) {
                this.addTerminalMessage('No scrape data available for summary report', 'warning');
                return;
            }
            
            // Display summary report in terminal
            this.addTerminalMessage('=== SCRAPER SUMMARY REPORT ===', 'success');
            this.addTerminalMessage(`Scrape Date: ${report.scrape_date} at ${report.scrape_time}`, 'info');
            this.addTerminalMessage(`Duration: ${report.duration_formatted}`, 'info');
            this.addTerminalMessage(`Total Vehicles: ${report.total_vehicles}`, 'info');
            this.addTerminalMessage(`Missing VINs: ${report.missing_vins}`, report.missing_vins > 0 ? 'warning' : 'info');
            this.addTerminalMessage(`Dealerships: ${report.dealerships_successful}/${report.dealerships_processed} successful`, 'info');
            
            if (report.total_errors > 0) {
                this.addTerminalMessage(`Errors: ${report.total_errors}`, 'error');
                report.errors.forEach(error => {
                    this.addTerminalMessage(`  - ${error}`, 'error');
                });
            }
            
            this.addTerminalMessage('=== END SUMMARY REPORT ===', 'success');
            
        } catch (error) {
            console.error('Error generating summary report:', error);
            this.addTerminalMessage(`Error generating summary report: ${error.message}`, 'error');
        }
    }
    
    showScheduleModal() {
        this.showModal('scheduleModal');
    }
    
    saveScheduleSettings() {
        // This would save schedule settings
        this.addTerminalMessage('Schedule settings saved', 'success');
        this.closeModal('scheduleModal');
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
        }
    }
    
    addTerminalMessage(message, type = 'info') {
        const terminal = document.getElementById('terminalOutput');
        if (!terminal) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        line.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message ${type}">${message}</span>
        `;
        
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
        
        // Keep only last 100 messages
        const lines = terminal.querySelectorAll('.terminal-line');
        if (lines.length > 100) {
            lines[0].remove();
        }
    }
    
    clearTerminal() {
        const terminal = document.getElementById('terminalOutput');
        if (terminal) {
            terminal.innerHTML = '';
            this.addTerminalMessage('Terminal cleared', 'info');
        }
    }
    
    startStatusPolling() {
        // Check status every 5 seconds
        setInterval(() => {
            this.checkScraperStatus();
        }, 5000);
        
        // Load logs every 10 seconds
        setInterval(() => {
            this.loadRecentLogs();
        }, 10000);
    }
    
    async loadRecentLogs() {
        try {
            const response = await fetch('/api/logs');
            const result = await response.json();
            
            if (result.logs && result.logs.length > 0) {
                // Add new log entries to terminal (simplified version)
                // In a full implementation, you'd track which logs have been shown
            }
            
        } catch (error) {
            // Silently handle log loading errors
        }
    }
}

// Initialize the application when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MinisFornumApp();
});

// Global function for inline event handlers
window.app = app;