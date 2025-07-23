#!/usr/bin/env python3
"""
Web-Based Scraper Interface - Production Ready
Replaces tkinter GUI with web interface while keeping all backend logic intact
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    # Import scraper components
    from batch_scraper import BatchScraper
    from normalizer import VehicleDataNormalizer
    from order_processor import OrderProcessor, OrderConfig
    from qr_processor import QRProcessor
    from apps_script_functions import AppsScriptProcessor, create_apps_script_processor
    from google_sheets_filters import GoogleSheetsFilters
    
    # Import verified dealerships
    from dealerships.verified_working_dealerships import get_production_ready_dealerships
    DEALERSHIP_CONFIGS = get_production_ready_dealerships()
    
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    DEALERSHIP_CONFIGS = {}

class WebScraperInterface:
    """Web-based interface for the scraper pipeline"""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.running = False
        
        # Pipeline components (same as original)
        self.batch_scraper = None
        self.normalizer = VehicleDataNormalizer()
        self.order_processor = None
        self.qr_processor = None
        self.apps_script_processor = None
        
        # State management
        self.current_operation = None
        self.operation_status = "idle"
        self.operation_log = []
        self.results = {}
        
        # Initialize components
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all pipeline components"""
        try:
            self.batch_scraper = BatchScraper()
            print("✅ Batch scraper initialized")
        except Exception as e:
            print(f"⚠️ Batch scraper init warning: {e}")
        
        try:
            self.order_processor = OrderProcessor(OrderConfig())
            print("✅ Order processor initialized")
        except Exception as e:
            print(f"⚠️ Order processor init warning: {e}")
        
        try:
            self.qr_processor = QRProcessor()
            print("✅ QR processor initialized")
        except Exception as e:
            print(f"⚠️ QR processor init warning: {e}")
        
        try:
            self.apps_script_processor = create_apps_script_processor()
            print("✅ Apps Script processor initialized")
        except Exception as e:
            print(f"⚠️ Apps Script processor init warning: {e}")
    
    def generate_html_interface(self):
        """Generate the main HTML interface"""
        dealership_options = ""
        for dealer_id, config in DEALERSHIP_CONFIGS.items():
            api_type = config.get('api_type', 'Unknown')
            brand = config.get('brand', 'Unknown')
            locality = config.get('locality', 'Unknown')
            dealership_options += f'<option value="{dealer_id}">{config["name"]} ({brand} - {locality}) - {api_type}</option>\n'
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silver Fox Marketing - Vehicle Scraper Pipeline</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .main-content {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .tabs {{
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .tab {{
            flex: 1;
            padding: 20px;
            background: #e9ecef;
            border: none;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .tab.active {{
            background: white;
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }}
        
        .tab-content {{
            padding: 30px;
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }}
        
        .section h3 {{
            color: #495057;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .dealership-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .dealership-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .dealership-card:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }}
        
        .dealership-card.selected {{
            border-color: #667eea;
            background: #f8f9ff;
        }}
        
        .dealership-name {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }}
        
        .dealership-details {{
            font-size: 0.9rem;
            color: #6c757d;
            line-height: 1.4;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #218838;
        }}
        
        .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }}
        
        .status-bar {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        
        .status-active {{
            background: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }}
        
        .status-error {{
            background: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }}
        
        .log-container {{
            background: #2d3748;
            color: #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.5;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            border-radius: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        .verification-panel {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }}
        
        .verification-panel.show {{
            display: block;
        }}
        
        .data-preview {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
            max-height: 300px;
            overflow: auto;
        }}
        
        .checkbox-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}
        
        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .loading {{
            animation: pulse 2s infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Silver Fox Marketing</h1>
            <p>Vehicle Scraper Pipeline - Production Interface</p>
        </div>
        
        <div class="main-content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('scraper')">🔍 Scraper</button>
                <button class="tab" onclick="showTab('pipeline')">⚙️ Pipeline</button>
                <button class="tab" onclick="showTab('results')">📊 Results</button>
                <button class="tab" onclick="showTab('settings')">⚙️ Settings</button>
            </div>
            
            <!-- Scraper Tab -->
            <div id="scraper" class="tab-content active">
                <div class="section">
                    <h3>🎯 Dealership Selection</h3>
                    <p>Select dealerships to scrape. Total available: {len(DEALERSHIP_CONFIGS)} production-ready dealerships.</p>
                    
                    <div class="controls">
                        <button class="btn btn-secondary" onclick="selectAllDealerships()">Select All</button>
                        <button class="btn btn-secondary" onclick="clearAllDealerships()">Clear All</button>
                        <button class="btn btn-secondary" onclick="selectByAPI()">Select by API</button>
                    </div>
                    
                    <div class="dealership-grid" id="dealershipGrid">
                        {self.generate_dealership_cards()}
                    </div>
                </div>
                
                <div class="section">
                    <h3>🚀 Scraping Controls</h3>
                    
                    <div class="controls">
                        <button class="btn btn-primary" onclick="startScraping()" id="startBtn">
                            ▶️ Start Scraping
                        </button>
                        <button class="btn btn-secondary" onclick="stopScraping()" id="stopBtn" disabled>
                            ⏹️ Stop Scraping
                        </button>
                        <button class="btn btn-success" onclick="exportResults()" id="exportBtn" disabled>
                            📤 Export Results
                        </button>
                    </div>
                    
                    <div class="status-bar" id="statusBar">
                        Status: Ready to scrape
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📋 Live Log</h3>
                    <div class="log-container" id="logContainer">
                        Ready to start scraping...\n
                    </div>
                </div>
            </div>
            
            <!-- Pipeline Tab -->
            <div id="pipeline" class="tab-content">
                <div class="section">
                    <h3>🔄 Complete Pipeline Execution</h3>
                    <p>Execute the full 7-stage pipeline with human verification checkpoints.</p>
                    
                    <div class="controls">
                        <button class="btn btn-primary" onclick="startPipeline()">🚀 Start Pipeline</button>
                        <button class="btn btn-secondary" onclick="pausePipeline()">⏸️ Pause Pipeline</button>
                    </div>
                    
                    <div class="pipeline-stages" id="pipelineStages">
                        <div class="stage" data-stage="1">
                            <div class="stage-header">📡 Stage 1: Data Collection</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="2">
                            <div class="stage-header">🔄 Stage 2: Data Normalization</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="3">
                            <div class="stage-header">📝 Stage 3: Order Processing</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="4">
                            <div class="stage-header">📊 Stage 4: Apps Script Integration</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="5">
                            <div class="stage-header">🏷️ Stage 5: QR Generation</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="6">
                            <div class="stage-header">✅ Stage 6: Quality Validation</div>
                            <div class="stage-status">Pending</div>
                        </div>
                        <div class="stage" data-stage="7">
                            <div class="stage-header">🎯 Stage 7: Final Export</div>
                            <div class="stage-status">Pending</div>
                        </div>
                    </div>
                </div>
                
                <div class="verification-panel" id="verificationPanel">
                    <h4>🔍 Human Verification Required</h4>
                    <p id="verificationMessage"></p>
                    <div class="data-preview" id="dataPreview"></div>
                    <div class="controls">
                        <button class="btn btn-success" onclick="approveVerification()">✅ Approve</button>
                        <button class="btn btn-secondary" onclick="rejectVerification()">❌ Reject</button>
                    </div>
                </div>
            </div>
            
            <!-- Results Tab -->
            <div id="results" class="tab-content">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="totalVehicles">0</div>
                        <div class="stat-label">Total Vehicles</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="completedDealerships">0</div>
                        <div class="stat-label">Completed Dealerships</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="successRate">0%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalTime">0s</div>
                        <div class="stat-label">Total Time</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📤 Export Options</h3>
                    <div class="controls">
                        <button class="btn btn-primary" onclick="exportCSV()">📄 Export CSV</button>
                        <button class="btn btn-primary" onclick="exportExcel()">📊 Export Excel</button>
                        <button class="btn btn-primary" onclick="exportJSON()">🔧 Export JSON</button>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📊 Results Preview</h3>
                    <div class="data-preview" id="resultsPreview">
                        No results available yet. Run a scraping operation first.
                    </div>
                </div>
            </div>
            
            <!-- Settings Tab -->
            <div id="settings" class="tab-content">
                <div class="section">
                    <h3>⚙️ Scraping Settings</h3>
                    <div class="settings-grid">
                        <label>Request Delay (seconds):</label>
                        <input type="number" id="requestDelay" value="2" min="1" max="10">
                        
                        <label>Timeout (seconds):</label>
                        <input type="number" id="timeout" value="30" min="10" max="120">
                        
                        <label>Max Concurrent:</label>
                        <input type="number" id="maxConcurrent" value="5" min="1" max="20">
                        
                        <label>Enable Verification:</label>
                        <input type="checkbox" id="enableVerification" checked>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📁 Data Management</h3>
                    <div class="controls">
                        <button class="btn btn-secondary" onclick="clearResults()">🗑️ Clear Results</button>
                        <button class="btn btn-secondary" onclick="resetSettings()">🔄 Reset Settings</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let selectedDealerships = [];
        let isRunning = false;
        let currentResults = {{}};
        
        // Tab management
        function showTab(tabName) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.remove('active');
            }});
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        // Dealership selection
        function selectAllDealerships() {{
            document.querySelectorAll('.dealership-card').forEach(card => {{
                card.classList.add('selected');
                selectedDealerships.push(card.dataset.dealerId);
            }});
            selectedDealerships = [...new Set(selectedDealerships)];
            updateSelectionCount();
        }}
        
        function clearAllDealerships() {{
            document.querySelectorAll('.dealership-card').forEach(card => {{
                card.classList.remove('selected');
            }});
            selectedDealerships = [];
            updateSelectionCount();
        }}
        
        function selectByAPI() {{
            const apiType = prompt('Enter API type (Algolia, DealerOn, SmartPath, DDC, Sitemap):');
            if (apiType) {{
                document.querySelectorAll('.dealership-card').forEach(card => {{
                    if (card.dataset.apiType.toLowerCase().includes(apiType.toLowerCase())) {{
                        card.classList.add('selected');
                        selectedDealerships.push(card.dataset.dealerId);
                    }}
                }});
                selectedDealerships = [...new Set(selectedDealerships)];
                updateSelectionCount();
            }}
        }}
        
        function toggleDealership(dealerId) {{
            const card = document.querySelector(`[data-dealer-id="${{dealerId}}"]`);
            if (card.classList.contains('selected')) {{
                card.classList.remove('selected');
                selectedDealerships = selectedDealerships.filter(id => id !== dealerId);
            }} else {{
                card.classList.add('selected');
                selectedDealerships.push(dealerId);
            }}
            updateSelectionCount();
        }}
        
        function updateSelectionCount() {{
            const count = selectedDealerships.length;
            document.querySelector('h3').innerHTML = `🎯 Dealership Selection (${{count}} selected)`;
        }}
        
        // Scraping operations
        async function startScraping() {{
            if (selectedDealerships.length === 0) {{
                alert('Please select at least one dealership to scrape.');
                return;
            }}
            
            isRunning = true;
            updateUI();
            
            try {{
                const response = await fetch('/start_scraping', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        dealerships: selectedDealerships,
                        settings: getSettings()
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    pollProgress();
                }} else {{
                    throw new Error(result.error);
                }}
            }} catch (error) {{
                console.error('Scraping failed:', error);
                updateLog(`❌ Scraping failed: ${{error.message}}`, 'error');
                isRunning = false;
                updateUI();
            }}
        }}
        
        async function stopScraping() {{
            const response = await fetch('/stop_scraping', {{ method: 'POST' }});
            const result = await response.json();
            
            isRunning = false;
            updateUI();
            updateLog('⏹️ Scraping stopped by user', 'warning');
        }}
        
        function getSettings() {{
            return {{
                requestDelay: parseInt(document.getElementById('requestDelay').value),
                timeout: parseInt(document.getElementById('timeout').value),
                maxConcurrent: parseInt(document.getElementById('maxConcurrent').value),
                enableVerification: document.getElementById('enableVerification').checked
            }};
        }}
        
        // UI updates
        function updateUI() {{
            document.getElementById('startBtn').disabled = isRunning;
            document.getElementById('stopBtn').disabled = !isRunning;
            document.getElementById('exportBtn').disabled = !currentResults.vehicles || currentResults.vehicles.length === 0;
            
            const statusBar = document.getElementById('statusBar');
            if (isRunning) {{
                statusBar.textContent = 'Status: Scraping in progress...';
                statusBar.className = 'status-bar status-active loading';
            }} else {{
                statusBar.textContent = 'Status: Ready to scrape';
                statusBar.className = 'status-bar';
            }}
        }}
        
        function updateLog(message, type = 'info') {{
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${{timestamp}}] ${{message}}\\n`;
            
            logContainer.textContent += logEntry;
            logContainer.scrollTop = logContainer.scrollHeight;
        }}
        
        function updateProgress(percentage, message = '') {{
            document.getElementById('progressFill').style.width = `${{percentage}}%`;
            if (message) {{
                updateLog(message);
            }}
        }}
        
        // Progress polling
        async function pollProgress() {{
            if (!isRunning) return;
            
            try {{
                const response = await fetch('/progress');
                const progress = await response.json();
                
                updateProgress(progress.percentage, progress.message);
                updateStats(progress.stats);
                
                if (progress.completed) {{
                    isRunning = false;
                    updateUI();
                    currentResults = progress.results;
                    updateResults();
                    updateLog('✅ Scraping completed successfully!', 'success');
                }} else {{
                    setTimeout(pollProgress, 1000);
                }}
            }} catch (error) {{
                console.error('Progress polling failed:', error);
                setTimeout(pollProgress, 5000); // Retry after 5 seconds
            }}
        }}
        
        function updateStats(stats) {{
            if (stats) {{
                document.getElementById('totalVehicles').textContent = stats.totalVehicles || 0;
                document.getElementById('completedDealerships').textContent = stats.completedDealerships || 0;
                document.getElementById('successRate').textContent = `${{(stats.successRate || 0).toFixed(1)}}%`;
                document.getElementById('totalTime').textContent = `${{stats.totalTime || 0}}s`;
            }}
        }}
        
        function updateResults() {{
            if (currentResults.vehicles && currentResults.vehicles.length > 0) {{
                const preview = document.getElementById('resultsPreview');
                const sample = currentResults.vehicles.slice(0, 5);
                
                let html = '<table style="width: 100%; border-collapse: collapse;">';
                html += '<tr style="background: #f8f9fa;">';
                
                // Table headers
                const headers = Object.keys(sample[0]);
                headers.forEach(header => {{
                    html += `<th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${{header}}</th>`;
                }});
                html += '</tr>';
                
                // Table rows
                sample.forEach(vehicle => {{
                    html += '<tr>';
                    headers.forEach(header => {{
                        html += `<td style="border: 1px solid #dee2e6; padding: 8px;">${{vehicle[header] || ''}}</td>`;
                    }});
                    html += '</tr>';
                }});
                
                html += '</table>';
                html += `<p style="margin-top: 10px; color: #6c757d;">Showing 5 of ${{currentResults.vehicles.length}} total vehicles</p>`;
                
                preview.innerHTML = html;
            }}
        }}
        
        // Export functions
        async function exportCSV() {{
            const response = await fetch('/export/csv');
            const blob = await response.blob();
            downloadFile(blob, 'scraping_results.csv');
        }}
        
        async function exportExcel() {{
            const response = await fetch('/export/excel');
            const blob = await response.blob();
            downloadFile(blob, 'scraping_results.xlsx');
        }}
        
        async function exportJSON() {{
            const response = await fetch('/export/json');
            const blob = await response.blob();
            downloadFile(blob, 'scraping_results.json');
        }}
        
        function downloadFile(blob, filename) {{
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        }}
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            updateUI();
            updateLog('🚀 Silver Fox Marketing Scraper Interface loaded');
            updateLog(`📊 ${{Object.keys({{}}).length}} production-ready dealerships available`);
        }});
    </script>
</body>
</html>
        """
        return html
    
    def generate_dealership_cards(self):
        """Generate HTML for dealership selection cards"""
        cards_html = ""
        
        for dealer_id, config in DEALERSHIP_CONFIGS.items():
            api_type = config.get('api_type', 'Unknown')
            brand = config.get('brand', 'Unknown')
            locality = config.get('locality', 'Unknown')
            
            cards_html += f'''
            <div class="dealership-card" data-dealer-id="{dealer_id}" data-api-type="{api_type}" onclick="toggleDealership('{dealer_id}')">
                <div class="dealership-name">{config["name"]}</div>
                <div class="dealership-details">
                    <strong>Brand:</strong> {brand}<br>
                    <strong>Location:</strong> {locality}<br>
                    <strong>API:</strong> {api_type}
                </div>
            </div>
            '''
        
        return cards_html
    
    def start_server(self):
        """Start the web server"""
        class ScraperHTTPHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.scraper_interface = kwargs.pop('scraper_interface', None)
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = self.scraper_interface.generate_html_interface()
                    self.wfile.write(html.encode())
                    return
                elif self.path == '/progress':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    progress = self.scraper_interface.get_progress()
                    self.wfile.write(json.dumps(progress).encode())
                    return
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path == '/start_scraping':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    result = self.scraper_interface.start_scraping_operation(data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                    return
                elif self.path == '/stop_scraping':
                    result = self.scraper_interface.stop_scraping_operation()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                    return
        
        handler = lambda *args, **kwargs: ScraperHTTPHandler(*args, scraper_interface=self, **kwargs)
        
        self.server = HTTPServer(('localhost', self.port), handler)
        self.running = True
        
        print(f"🌐 Starting web server on http://localhost:{self.port}")
        
        # Open browser
        webbrowser.open(f'http://localhost:{self.port}')
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\\n🛑 Server stopped by user")
            self.running = False
    
    def start_scraping_operation(self, data):
        """Start scraping operation in background thread"""
        try:
            dealerships = data.get('dealerships', [])
            settings = data.get('settings', {})
            
            # Start background thread
            thread = threading.Thread(target=self.run_scraping, args=(dealerships, settings))
            thread.daemon = True
            thread.start()
            
            self.operation_status = "running"
            self.operation_log.append("🚀 Scraping operation started")
            
            return {"success": True, "message": "Scraping started"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_scraping(self, dealerships, settings):
        """Run the actual scraping operation"""
        try:
            self.operation_log.append(f"📊 Selected {len(dealerships)} dealerships")
            
            # Initialize batch scraper with settings
            if self.batch_scraper:
                # Configure scraper settings
                self.batch_scraper.configure_settings(settings)
                
                # Run scraping
                results = self.batch_scraper.scrape_multiple_dealerships(dealerships)
                
                # Normalize results
                normalized_results = self.normalizer.normalize_dataframe(results)
                
                self.results = {
                    'vehicles': normalized_results.to_dict('records'),
                    'total_count': len(normalized_results),
                    'dealerships_processed': len(dealerships),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.operation_status = "completed"
                self.operation_log.append(f"✅ Scraping completed: {len(normalized_results)} vehicles")
            else:
                raise Exception("Batch scraper not initialized")
                
        except Exception as e:
            self.operation_status = "error"
            self.operation_log.append(f"❌ Scraping failed: {str(e)}")
    
    def stop_scraping_operation(self):
        """Stop current scraping operation"""
        self.operation_status = "stopped"
        self.operation_log.append("⏹️ Scraping stopped by user")
        return {"success": True, "message": "Scraping stopped"}
    
    def get_progress(self):
        """Get current progress status"""
        # Calculate progress percentage
        percentage = 0
        if self.operation_status == "running":
            percentage = 50  # Simplified progress
        elif self.operation_status == "completed":
            percentage = 100
        
        return {
            "percentage": percentage,
            "message": self.operation_log[-1] if self.operation_log else "Ready",
            "completed": self.operation_status in ["completed", "error", "stopped"],
            "results": self.results,
            "stats": {
                "totalVehicles": len(self.results.get('vehicles', [])),
                "completedDealerships": self.results.get('dealerships_processed', 0),
                "successRate": 100.0 if self.operation_status == "completed" else 0,
                "totalTime": 0  # TODO: Track actual time
            }
        }

def main():
    """Main function to start the web interface"""
    print("🚗 Silver Fox Marketing - Web Scraper Interface")
    print("=" * 60)
    print(f"📊 Available dealerships: {len(DEALERSHIP_CONFIGS)}")
    print("🌐 Starting web server...")
    
    interface = WebScraperInterface()
    
    try:
        interface.start_server()
    except Exception as e:
        print(f"❌ Server failed to start: {e}")

if __name__ == "__main__":
    main()