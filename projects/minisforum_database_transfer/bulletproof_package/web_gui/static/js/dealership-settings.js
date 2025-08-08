// ==================== Dealership Settings Functionality ====================

// Add methods to the MinisFornumApp prototype
MinisFornumApp.prototype.initializeDealershipSettings = async function() {
    console.log('Initializing dealership settings...');
    
    // Show loading state
    const grid = document.getElementById('dealershipSettingsGrid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i>Loading dealership settings...</div>';
    
    try {
        const response = await fetch('/api/dealership-settings');
        const data = await response.json();
        
        if (data.success) {
            this.renderDealershipSettings(data.dealerships);
            this.setupDealershipSettingsListeners();
        } else {
            throw new Error(data.error || 'Failed to load settings');
        }
    } catch (error) {
        console.error('Error loading dealership settings:', error);
        grid.innerHTML = '<div class="error-message">Failed to load dealership settings. Please try again.</div>';
    }
};

MinisFornumApp.prototype.renderDealershipSettings = function(dealerships) {
    const grid = document.getElementById('dealershipSettingsGrid');
    if (!grid) return;
    
    // Store dealerships for filtering
    this.dealershipSettings = dealerships;
    
    // Build HTML for all dealership cards
    const html = dealerships.map(dealership => {
        const isNew = dealership.vehicle_types.includes('new');
        const isUsed = dealership.vehicle_types.includes('used');
        const isCertified = dealership.vehicle_types.includes('certified');
        
        const filterType = (isNew && isUsed) ? 'both' : (isNew ? 'new' : (isUsed ? 'used' : 'none'));
        
        return `
            <div class="dealership-settings-card" data-id="${dealership.id}" data-name="${dealership.name}" data-filter-type="${filterType}">
                <h3>
                    ${dealership.name}
                    <span class="status-indicator"></span>
                </h3>
                <div class="vehicle-info">
                    <small>${dealership.vehicle_count || 0} vehicles • Last import: ${dealership.last_import ? new Date(dealership.last_import).toLocaleDateString() : 'Never'}</small>
                </div>
                <div class="vehicle-type-selector">
                    <label>Vehicle Types to Process:</label>
                    <div class="type-toggle-group">
                        <div class="type-toggle">
                            <input type="checkbox" id="new_${dealership.id}" value="new" ${isNew ? 'checked' : ''}>
                            <label for="new_${dealership.id}">New</label>
                        </div>
                        <div class="type-toggle">
                            <input type="checkbox" id="used_${dealership.id}" value="used" ${isUsed ? 'checked' : ''}>
                            <label for="used_${dealership.id}">Used</label>
                        </div>
                        <div class="type-toggle">
                            <input type="checkbox" id="certified_${dealership.id}" value="certified" ${isCertified ? 'checked' : ''}>
                            <label for="certified_${dealership.id}">Certified</label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    grid.innerHTML = html;
    
    // Update filter counts
    this.updateFilterCounts();
};

MinisFornumApp.prototype.setupDealershipSettingsListeners = function() {
    // Search functionality
    const searchInput = document.getElementById('dealershipSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            this.filterDealershipSettings(e.target.value);
        });
    }
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            this.filterDealershipSettingsByType(e.target.dataset.filter);
        });
    });
    
    // Checkbox changes
    document.querySelectorAll('.dealership-settings-card input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const card = e.target.closest('.dealership-settings-card');
            card.classList.add('modified');
            this.updateDealershipFilterType(card);
        });
    });
    
    // Save all button
    const saveBtn = document.getElementById('saveAllSettingsBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => this.saveAllDealershipSettings());
    }
};

MinisFornumApp.prototype.filterDealershipSettings = function(searchTerm) {
    const cards = document.querySelectorAll('.dealership-settings-card');
    const term = searchTerm.toLowerCase();
    
    cards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        if (name.includes(term)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
};

MinisFornumApp.prototype.filterDealershipSettingsByType = function(filterType) {
    const cards = document.querySelectorAll('.dealership-settings-card');
    
    cards.forEach(card => {
        if (filterType === 'all' || card.dataset.filterType === filterType) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
};

MinisFornumApp.prototype.updateDealershipFilterType = function(card) {
    const isNew = card.querySelector('input[value="new"]').checked;
    const isUsed = card.querySelector('input[value="used"]').checked;
    
    const filterType = (isNew && isUsed) ? 'both' : (isNew ? 'new' : (isUsed ? 'used' : 'none'));
    card.dataset.filterType = filterType;
};

MinisFornumApp.prototype.updateFilterCounts = function() {
    const cards = document.querySelectorAll('.dealership-settings-card');
    let newCount = 0, usedCount = 0, bothCount = 0;
    
    cards.forEach(card => {
        const filterType = card.dataset.filterType;
        if (filterType === 'new') newCount++;
        else if (filterType === 'used') usedCount++;
        else if (filterType === 'both') bothCount++;
    });
    
    // Update button labels
    const newBtn = document.querySelector('.filter-btn[data-filter="new"]');
    const usedBtn = document.querySelector('.filter-btn[data-filter="used"]');
    const bothBtn = document.querySelector('.filter-btn[data-filter="both"]');
    
    if (newBtn) newBtn.textContent = `New Only (${newCount})`;
    if (usedBtn) usedBtn.textContent = `Used Only (${usedCount})`;
    if (bothBtn) bothBtn.textContent = `New & Used (${bothCount})`;
};

MinisFornumApp.prototype.saveAllDealershipSettings = async function() {
    const modifiedCards = document.querySelectorAll('.dealership-settings-card.modified');
    
    if (modifiedCards.length === 0) {
        alert('No changes to save');
        return;
    }
    
    const saveBtn = document.getElementById('saveAllSettingsBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const card of modifiedCards) {
        const dealershipId = card.dataset.id;
        const vehicleTypes = [];
        
        card.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            vehicleTypes.push(checkbox.value);
        });
        
        try {
            const response = await fetch(`/api/dealership-settings/${dealershipId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_types: vehicleTypes })
            });
            
            if (response.ok) {
                card.classList.remove('modified');
                successCount++;
            } else {
                errorCount++;
            }
        } catch (error) {
            console.error('Error saving dealership settings:', error);
            errorCount++;
        }
    }
    
    saveBtn.disabled = false;
    saveBtn.innerHTML = '<i class="fas fa-save"></i> Save All Changes';
    
    if (errorCount === 0) {
        alert(`Successfully saved settings for ${successCount} dealerships`);
    } else {
        alert(`Saved ${successCount} dealerships, but ${errorCount} failed. Please try again.`);
    }
    
    // Update filter counts after saving
    this.updateFilterCounts();
};

MinisFornumApp.prototype.bulkUpdateSettings = async function(settingType) {
    const vehicleTypes = settingType === 'both' ? ['new', 'used'] : [settingType];
    
    if (!confirm(`Set all dealerships to process ${settingType === 'both' ? 'New & Used' : settingType + ' Only'} vehicles?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/dealership-settings/bulk', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vehicle_types: vehicleTypes })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Successfully updated ${data.updated_count} dealerships`);
            // Reload settings to reflect changes
            this.initializeDealershipSettings();
        } else {
            throw new Error(data.error || 'Failed to update settings');
        }
    } catch (error) {
        console.error('Error bulk updating settings:', error);
        alert('Failed to update settings. Please try again.');
    }
};

// Make bulkUpdateSettings available globally for button onclick
window.app = window.app || {};
window.app.bulkUpdateSettings = function(settingType) {
    // Use the global app instance created in app.js
    if (typeof app !== 'undefined' && app.bulkUpdateSettings) {
        app.bulkUpdateSettings(settingType);
    } else if (window.appInstance && window.appInstance.bulkUpdateSettings) {
        window.appInstance.bulkUpdateSettings(settingType);
    } else {
        console.error('App instance not found for bulk update settings');
    }
};

// Initialize dealership settings when the tab is clicked
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for app to initialize
    setTimeout(() => {
        const dealershipTab = document.querySelector('[data-tab="dealership-settings"]');
        if (dealershipTab) {
            dealershipTab.addEventListener('click', () => {
                // Get the actual app instance (created in app.js)
                if (typeof app !== 'undefined' && app && !app.dealershipSettingsInitialized) {
                    app.initializeDealershipSettings();
                    app.dealershipSettingsInitialized = true;
                }
            });
        }
        
        // Store app instance globally for bulk update functions
        if (typeof app !== 'undefined') {
            window.appInstance = app;
        }
    }, 500);
});