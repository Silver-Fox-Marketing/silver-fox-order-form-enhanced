#!/usr/bin/env python3
"""
Simple Web-Based Scraper Interface - Quick Test Version
Minimal web interface to test core scraping functionality
"""

import os
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
from pathlib import Path

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    # Import scraper components
    from batch_scraper import BatchScraper
    from normalizer import VehicleDataNormalizer
    from dealerships.verified_working_dealerships import get_production_ready_dealerships
    DEALERSHIP_CONFIGS = get_production_ready_dealerships()
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    DEALERSHIP_CONFIGS = {}

class SimpleScraperHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/status':
            self.serve_status()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/scrape':
            self.handle_scrape_request()
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        """Serve the main scraper interface"""
        dealership_options = ""
        for dealer_id, config in DEALERSHIP_CONFIGS.items():
            dealership_options += f'<option value="{dealer_id}">{config["name"]} ({config["brand"]})</option>'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Silver Fox Marketing - Vehicle Scraper</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        select {{ width: 100%; padding: 10px; font-size: 16px; margin-bottom: 20px; }}
        button {{ padding: 12px 24px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px; }}
        .btn-primary {{ background: #007bff; color: white; }}
        .btn-primary:hover {{ background: #0056b3; }}
        .btn-success {{ background: #28a745; color: white; }}
        .btn-success:hover {{ background: #1e7e34; }}
        .status {{ padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .status-info {{ background: #d1ecf1; color: #0c5460; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        .log {{ background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 5px; font-family: monospace; height: 300px; overflow-y: auto; }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 Silver Fox Marketing - Vehicle Scraper</h1>
        
        <div class="section">
            <h3>Select Dealerships to Scrape</h3>
            <select id="dealershipSelect" multiple size="10">
                {dealership_options}
            </select>
            <div>
                <button class="btn-primary" onclick="selectAll()">Select All</button>
                <button class="btn-primary" onclick="clearAll()">Clear All</button>
            </div>
        </div>
        
        <div class="section">
            <h3>Scraping Controls</h3>
            <button id="scrapeBtn" class="btn-success" onclick="startScraping()">🚀 Start Scraping</button>
            <button id="exportBtn" class="btn-primary hidden" onclick="exportResults()">📤 Export Results</button>
        </div>
        
        <div id="status" class="status status-info">
            Ready to scrape. Select dealerships and click "Start Scraping".
        </div>
        
        <div class="section">
            <h3>Live Log</h3>
            <div id="log" class="log">Ready to start scraping...\\n</div>
        </div>
    </div>

    <script>
        let isRunning = false;
        let results = null;
        
        function selectAll() {{
            const select = document.getElementById('dealershipSelect');
            for (let i = 0; i < select.options.length; i++) {{
                select.options[i].selected = true;
            }}
        }}
        
        function clearAll() {{
            const select = document.getElementById('dealershipSelect');
            for (let i = 0; i < select.options.length; i++) {{
                select.options[i].selected = false;
            }}
        }}
        
        function log(message) {{
            const logEl = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            logEl.textContent += `[${{timestamp}}] ${{message}}\\n`;
            logEl.scrollTop = logEl.scrollHeight;
        }}
        
        function updateStatus(message, type = 'info') {{
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = `status status-${{type}}`;
        }}
        
        async function startScraping() {{
            const select = document.getElementById('dealershipSelect');
            const selectedOptions = Array.from(select.selectedOptions);
            
            if (selectedOptions.length === 0) {{
                alert('Please select at least one dealership.');
                return;
            }}
            
            const selectedDealerships = selectedOptions.map(option => option.value);
            
            isRunning = true;
            document.getElementById('scrapeBtn').disabled = true;
            document.getElementById('exportBtn').classList.add('hidden');
            
            updateStatus('Starting scraping operation...', 'info');
            log(`Starting scrape of ${{selectedDealerships.length}} dealerships`);
            
            try {{
                const response = await fetch('/scrape', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        dealerships: selectedDealerships
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    updateStatus(`Scraping completed! Found ${{result.total_vehicles}} vehicles`, 'success');
                    log(`✅ Scraping completed successfully`);
                    log(`📊 Total vehicles: ${{result.total_vehicles}}`);
                    log(`🏢 Dealerships processed: ${{result.dealerships_processed}}`);
                    
                    results = result;
                    document.getElementById('exportBtn').classList.remove('hidden');
                }} else {{
                    throw new Error(result.error || 'Unknown error');
                }}
            }} catch (error) {{
                updateStatus(`Scraping failed: ${{error.message}}`, 'error');
                log(`❌ Error: ${{error.message}}`);
            }} finally {{
                isRunning = false;
                document.getElementById('scrapeBtn').disabled = false;
            }}
        }}
        
        function exportResults() {{
            if (results && results.csv_data) {{
                const blob = new Blob([results.csv_data], {{ type: 'text/csv' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `scraping_results_${{new Date().toISOString().split('T')[0]}}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                log('📤 Results exported to CSV file');
            }}
        }}
        
        // Initialize
        log('🚀 Silver Fox Marketing Scraper Interface loaded');
        log(`📊 ${{document.getElementById('dealershipSelect').options.length}} dealerships available`);
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_scrape_request(self):
        """Handle scraping request"""
        try:
            # Read request data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            dealerships = data.get('dealerships', [])
            
            # Run scraping (this is a simplified version)
            print(f"🚀 Starting scrape of {len(dealerships)} dealerships")
            
            # Initialize components
            try:
                batch_scraper = BatchScraper()
                normalizer = VehicleDataNormalizer()
                
                # Run scraping for selected dealerships
                all_results = []
                processed_count = 0
                
                for dealer_id in dealerships:
                    if dealer_id in DEALERSHIP_CONFIGS:
                        print(f"📡 Scraping {DEALERSHIP_CONFIGS[dealer_id]['name']}")
                        try:
                            dealer_results = batch_scraper.scrape_single_dealership(dealer_id, DEALERSHIP_CONFIGS[dealer_id])
                            if dealer_results:
                                all_results.extend(dealer_results)
                                processed_count += 1
                                print(f"✅ {DEALERSHIP_CONFIGS[dealer_id]['name']}: {len(dealer_results)} vehicles")
                        except Exception as e:
                            print(f"❌ {DEALERSHIP_CONFIGS[dealer_id]['name']}: {str(e)}")
                
                # Normalize results
                if all_results:
                    import pandas as pd
                    df = pd.DataFrame(all_results)
                    normalized_df = normalizer.normalize_dataframe(df)
                    
                    # Convert to CSV for export
                    csv_data = normalized_df.to_csv(index=False)
                    
                    result = {
                        'success': True,
                        'total_vehicles': len(normalized_df),
                        'dealerships_processed': processed_count,
                        'csv_data': csv_data
                    }
                else:
                    result = {
                        'success': False,
                        'error': 'No vehicles found'
                    }
                
            except Exception as e:
                result = {
                    'success': False,
                    'error': f'Scraping failed: {str(e)}'
                }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def serve_status(self):
        """Serve current status"""
        status = {
            'dealerships_available': len(DEALERSHIP_CONFIGS),
            'system_status': 'ready'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())

def main():
    """Start the simple web scraper"""
    port = 8080
    
    print("🚗 Silver Fox Marketing - Simple Web Scraper")
    print("=" * 50)
    print(f"📊 Available dealerships: {len(DEALERSHIP_CONFIGS)}")
    print(f"🌐 Starting server on http://localhost:{port}")
    
    try:
        server = HTTPServer(('localhost', port), SimpleScraperHandler)
        
        # Open browser
        webbrowser.open(f'http://localhost:{port}')
        
        print("🚀 Server running! Press Ctrl+C to stop.")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed: {e}")

if __name__ == "__main__":
    main()