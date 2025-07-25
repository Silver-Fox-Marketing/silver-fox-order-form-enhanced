#!/usr/bin/env python3
"""
MinisForum Database Web GUI
==========================

Local web-based control interface for the dealership database system.
Provides visual dealership management, scraper control, and report generation.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time

# Add the scripts directory to Python path for imports
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import our existing modules
from database_connection import db_manager
from csv_importer_complete import CompleteCSVImporter
from order_processing_integration import OrderProcessingIntegrator
from qr_code_generator import QRCodeGenerator
from data_exporter import DataExporter

# Flask app setup
app = Flask(__name__)
app.secret_key = 'silver_fox_marketing_minisforum_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScraperController:
    """Controls scraper operations and manages system state"""
    
    def __init__(self):
        self.csv_importer = CompleteCSVImporter()
        self.order_processor = OrderProcessingIntegrator()
        self.qr_generator = QRCodeGenerator()
        self.data_exporter = DataExporter()
        self.scraper_running = False
        self.last_scrape_time = None
        self.scrape_results = {}
        
    def get_dealership_configs(self):
        """Get all dealership configurations"""
        try:
            configs = db_manager.execute_query("""
                SELECT name, filtering_rules, output_rules, qr_output_path, is_active, updated_at
                FROM dealership_configs 
                ORDER BY name
            """)
            
            for config in configs:
                # Parse JSON safely
                try:
                    config['filtering_rules'] = json.loads(config['filtering_rules']) if config['filtering_rules'] else {}
                    config['output_rules'] = json.loads(config['output_rules']) if config['output_rules'] else {}
                except json.JSONDecodeError:
                    config['filtering_rules'] = {}
                    config['output_rules'] = {}
            
            return configs
        except Exception as e:
            logger.error(f"Failed to get dealership configs: {e}")
            return []
    
    def update_dealership_config(self, dealership_name, filtering_rules, is_active=True):
        """Update dealership configuration"""
        try:
            db_manager.execute_query("""
                UPDATE dealership_configs 
                SET filtering_rules = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """, (json.dumps(filtering_rules), is_active, dealership_name))
            
            return True
        except Exception as e:
            logger.error(f"Failed to update dealership config: {e}")
            return False
    
    def run_scraper(self, selected_dealerships=None, csv_file_path=None):
        """Run the complete scraper pipeline"""
        try:
            self.scraper_running = True
            self.scrape_results = {
                'start_time': datetime.now(),
                'dealerships': {},
                'total_vehicles': 0,
                'errors': [],
                'duration': 0,
                'missing_vins': 0
            }
            
            logger.info("Starting scraper pipeline...")
            
            # Step 1: Import CSV data
            if csv_file_path and os.path.exists(csv_file_path):
                logger.info(f"Importing CSV: {csv_file_path}")
                import_result = self.csv_importer.import_csv(csv_file_path)
                
                if import_result and import_result.get('success'):
                    self.scrape_results['total_vehicles'] = import_result.get('processed', 0)
                    self.scrape_results['missing_vins'] = import_result.get('missing_vins', 0)
                    logger.info(f"CSV import successful: {import_result['processed']} vehicles")
                else:
                    raise Exception("CSV import failed")
            
            # Step 2: Process selected dealerships
            active_dealerships = selected_dealerships or [d['name'] for d in self.get_dealership_configs() if d['is_active']]
            
            for dealership in active_dealerships:
                try:
                    logger.info(f"Processing dealership: {dealership}")
                    
                    # Create order processing job
                    job = self.order_processor.create_order_processing_job(dealership)
                    
                    if job and job.get('job_id'):
                        self.scrape_results['dealerships'][dealership] = {
                            'job_id': job['job_id'],
                            'vehicle_count': job.get('vehicle_count', 0),
                            'qr_generated': job.get('qr_generation', {}).get('success', 0),
                            'export_file': job.get('export_file'),
                            'status': 'completed'
                        }
                        logger.info(f"Completed {dealership}: {job['vehicle_count']} vehicles")
                    else:
                        self.scrape_results['dealerships'][dealership] = {
                            'status': 'failed',
                            'error': 'Job creation failed'
                        }
                        
                except Exception as e:
                    logger.error(f"Error processing {dealership}: {e}")
                    self.scrape_results['dealerships'][dealership] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    self.scrape_results['errors'].append(f"{dealership}: {str(e)}")
            
            # Calculate duration
            self.scrape_results['end_time'] = datetime.now()
            self.scrape_results['duration'] = (self.scrape_results['end_time'] - self.scrape_results['start_time']).total_seconds()
            
            self.last_scrape_time = self.scrape_results['end_time']
            logger.info(f"Scraper pipeline completed in {self.scrape_results['duration']:.1f} seconds")
            
            return self.scrape_results
            
        except Exception as e:
            logger.error(f"Scraper pipeline failed: {e}")
            self.scrape_results['errors'].append(str(e))
            return self.scrape_results
        finally:
            self.scraper_running = False
    
    def generate_adobe_report(self, dealerships=None):
        """Generate Adobe-ready export files"""
        try:
            if not dealerships:
                dealerships = [d['name'] for d in self.get_dealership_configs() if d['is_active']]
            
            export_files = []
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for dealership in dealerships:
                export_file = self.data_exporter.export_dealership_data(
                    dealership, 
                    f"exports/adobe_export_{dealership.replace(' ', '_')}_{timestamp}.csv"
                )
                if export_file:
                    export_files.append(export_file)
            
            return export_files
        except Exception as e:
            logger.error(f"Adobe report generation failed: {e}")
            return []
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        try:
            if not self.scrape_results:
                return None
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'scrape_date': self.scrape_results['start_time'].strftime('%Y-%m-%d'),
                'scrape_time': self.scrape_results['start_time'].strftime('%H:%M:%S'),
                'duration_seconds': self.scrape_results['duration'],
                'duration_formatted': f"{self.scrape_results['duration']:.1f} seconds",
                'total_vehicles': self.scrape_results['total_vehicles'],
                'missing_vins': self.scrape_results['missing_vins'],
                'dealerships_processed': len(self.scrape_results['dealerships']),
                'dealerships_successful': len([d for d in self.scrape_results['dealerships'].values() if d.get('status') == 'completed']),
                'dealerships_failed': len([d for d in self.scrape_results['dealerships'].values() if d.get('status') == 'failed']),
                'total_errors': len(self.scrape_results['errors']),
                'dealership_details': [],
                'errors': self.scrape_results['errors']
            }
            
            for name, details in self.scrape_results['dealerships'].items():
                report['dealership_details'].append({
                    'name': name,
                    'vehicle_count': details.get('vehicle_count', 0),
                    'qr_generated': details.get('qr_generated', 0),
                    'status': details.get('status', 'unknown'),
                    'export_file': details.get('export_file')
                })
            
            return report
        except Exception as e:
            logger.error(f"Summary report generation failed: {e}")
            return None

# Global scraper controller
scraper_controller = ScraperController()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/dealerships')
def get_dealerships():
    """API endpoint to get dealership configurations"""
    configs = scraper_controller.get_dealership_configs()
    return jsonify(configs)

@app.route('/api/dealerships/<dealership_name>', methods=['POST'])
def update_dealership(dealership_name):
    """API endpoint to update dealership configuration"""
    data = request.get_json()
    
    filtering_rules = data.get('filtering_rules', {})
    is_active = data.get('is_active', True)
    
    success = scraper_controller.update_dealership_config(dealership_name, filtering_rules, is_active)
    
    if success:
        return jsonify({'success': True, 'message': 'Dealership updated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update dealership'}), 500

@app.route('/api/scraper/start', methods=['POST'])
def start_scraper():
    """API endpoint to start scraper"""
    if scraper_controller.scraper_running:
        return jsonify({'success': False, 'message': 'Scraper already running'}), 400
    
    data = request.get_json()
    selected_dealerships = data.get('dealerships', [])
    csv_file_path = data.get('csv_file_path')
    
    # Run scraper in background thread
    def run_scraper_thread():
        scraper_controller.run_scraper(selected_dealerships, csv_file_path)
    
    thread = threading.Thread(target=run_scraper_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Scraper started successfully'})

@app.route('/api/scraper/status')
def scraper_status():
    """API endpoint to get scraper status"""
    return jsonify({
        'running': scraper_controller.scraper_running,
        'last_scrape': scraper_controller.last_scrape_time.isoformat() if scraper_controller.last_scrape_time else None,
        'results': scraper_controller.scrape_results
    })

@app.route('/api/reports/adobe')
def generate_adobe_report():
    """API endpoint to generate Adobe report"""
    dealerships = request.args.getlist('dealerships')
    files = scraper_controller.generate_adobe_report(dealerships if dealerships else None)
    
    return jsonify({
        'success': True,
        'files': files,
        'count': len(files)
    })

@app.route('/api/reports/summary')
def get_summary_report():
    """API endpoint to get summary report"""
    report = scraper_controller.generate_summary_report()
    
    if report:
        return jsonify(report)
    else:
        return jsonify({'error': 'No scrape data available'}), 404

@app.route('/api/logs')
def get_logs():
    """API endpoint to get recent log entries"""
    try:
        log_file = 'web_gui.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Return last 100 lines
                return jsonify({'logs': lines[-100:]})
        else:
            return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('exports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting MinisForum Database Web GUI")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True)