#!/usr/bin/env python3
"""
Silver Fox Scraper Database Integration
======================================
Bridges the scraper system with the PostgreSQL database on MinisForum PC
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Add paths for both systems
sys.path.append(os.path.join(os.path.dirname(__file__), 'silverfox_scraper_system/silverfox_system'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/scripts'))

# Import from database system
from database_connection import db_manager
from order_processing_integration import OrderProcessingIntegrator
from qr_code_generator import QRCodeGenerator

# Import from scraper system
from core.scrapers.base.dealership_base import DealershipScraper
from core.data_processing.normalizer import VehicleNormalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScraperDatabaseBridge:
    """Integrates Silver Fox scraper system with PostgreSQL database"""
    
    def __init__(self):
        self.db = db_manager
        self.order_processor = OrderProcessingIntegrator(self.db)
        self.qr_generator = QRCodeGenerator(self.db)
        self.normalizer = VehicleNormalizer()
        
        # Paths
        self.scraper_config_path = Path("silverfox_scraper_system/silverfox_system/config")
        self.output_path = Path("output_data")
        self.output_path.mkdir(exist_ok=True)
        
    def run_scraper_and_import(self, dealership_name: str) -> Dict[str, Any]:
        """Run a scraper and import results directly to PostgreSQL"""
        try:
            logger.info(f"Running scraper for {dealership_name}")
            
            # Import the appropriate scraper
            scraper_module_name = dealership_name.lower().replace(' ', '').replace('.', '')
            
            # Try different scraper variations
            scraper = None
            for suffix in ['_working', '_optimized', '_production', '']:
                try:
                    module_path = f"core.scrapers.dealerships.{scraper_module_name}{suffix}"
                    module = __import__(module_path, fromlist=['create_scraper'])
                    scraper = module.create_scraper()
                    break
                except (ImportError, AttributeError):
                    continue
            
            if not scraper:
                logger.error(f"No scraper found for {dealership_name}")
                return {'success': False, 'error': 'Scraper not found'}
            
            # Run the scraper
            scraper_result = scraper.process()
            
            if not scraper_result or 'vehicles' not in scraper_result:
                return {'success': False, 'error': 'No vehicles found'}
            
            vehicles = scraper_result['vehicles']
            logger.info(f"Found {len(vehicles)} vehicles")
            
            # Import to database
            import_result = self._import_vehicles_to_db(vehicles, dealership_name)
            
            return {
                'success': True,
                'vehicles_scraped': len(vehicles),
                'vehicles_imported': import_result['imported_count'],
                'dealership': dealership_name
            }
            
        except Exception as e:
            logger.error(f"Error running scraper for {dealership_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _import_vehicles_to_db(self, vehicles: List[Dict], dealership_name: str) -> Dict:
        """Import scraped vehicles to PostgreSQL database"""
        try:
            # First, import to raw_vehicle_data
            raw_data = []
            for vehicle in vehicles:
                raw_data.append((
                    vehicle.get('vin'),
                    vehicle.get('stock'),
                    vehicle.get('type', 'Unknown'),
                    vehicle.get('year'),
                    vehicle.get('make'),
                    vehicle.get('model'),
                    vehicle.get('trim'),
                    vehicle.get('exterior_color'),
                    vehicle.get('status'),
                    float(vehicle.get('price', 0)) if vehicle.get('price') else None,
                    vehicle.get('body_style'),
                    vehicle.get('fuel_type'),
                    float(vehicle.get('msrp', 0)) if vehicle.get('msrp') else None,
                    vehicle.get('date_in_stock'),
                    vehicle.get('street_address'),
                    vehicle.get('locality'),
                    vehicle.get('postal_code'),
                    vehicle.get('region'),
                    vehicle.get('country'),
                    dealership_name,
                    vehicle.get('url')
                ))
            
            # Batch insert raw data
            raw_count = self.db.execute_batch_insert(
                'raw_vehicle_data',
                ['vin', 'stock', 'type', 'year', 'make', 'model', 'trim', 
                 'ext_color', 'status', 'price', 'body_style', 'fuel_type',
                 'msrp', 'date_in_stock', 'street_address', 'locality',
                 'postal_code', 'region', 'country', 'location', 'vehicle_url'],
                raw_data
            )
            
            # Now process and insert normalized data
            normalized_data = []
            for vehicle in vehicles:
                # Normalize status
                status = vehicle.get('status', '').lower()
                if 'new' in status:
                    condition = 'new'
                elif 'pre-owned' in status or 'used' in status:
                    condition = 'po'
                elif 'certified' in status:
                    condition = 'cpo'
                else:
                    condition = 'onlot'
                
                normalized_data.append((
                    vehicle.get('vin'),
                    vehicle.get('stock'),
                    condition,
                    vehicle.get('year'),
                    vehicle.get('make'),
                    vehicle.get('model'),
                    vehicle.get('trim'),
                    vehicle.get('status'),
                    float(vehicle.get('price', 0)) if vehicle.get('price') else None,
                    float(vehicle.get('msrp', 0)) if vehicle.get('msrp') else None,
                    vehicle.get('date_in_stock'),
                    dealership_name,
                    vehicle.get('url')
                ))
            
            # Upsert normalized data
            norm_count = self.db.upsert_data(
                'normalized_vehicle_data',
                ['vin', 'stock', 'vehicle_condition', 'year', 'make', 'model',
                 'trim', 'status', 'price', 'msrp', 'date_in_stock', 
                 'location', 'vehicle_url'],
                normalized_data,
                conflict_columns=['vin', 'location'],
                update_columns=['stock', 'vehicle_condition', 'price', 'status', 
                               'last_seen_date', 'updated_at']
            )
            
            # Update VIN history
            vin_history = []
            for vehicle in vehicles:
                vin_history.append((
                    vehicle.get('vin'),
                    dealership_name,
                    datetime.now().date()
                ))
            
            self.db.execute_batch_insert(
                'vin_history',
                ['vin', 'dealership_name', 'scan_date'],
                vin_history
            )
            
            # Run VACUUM ANALYZE for performance
            self.db.vacuum_analyze('normalized_vehicle_data')
            
            return {
                'imported_count': norm_count,
                'raw_count': raw_count
            }
            
        except Exception as e:
            logger.error(f"Failed to import vehicles: {e}")
            return {'imported_count': 0, 'raw_count': 0}
    
    def create_order_and_export(self, dealership_name: str, job_type: str = "standard") -> Dict:
        """Create an order processing job and export data for Adobe"""
        try:
            # Create order processing job
            job_result = self.order_processor.create_order_processing_job(
                dealership_name, job_type
            )
            
            if not job_result.get('success'):
                return job_result
            
            # Export data for Adobe
            export_file = job_result['export_file']
            logger.info(f"Order processed successfully. Export file: {export_file}")
            
            # Generate QR codes if needed
            if job_result.get('vehicles'):
                qr_results = []
                for vehicle in job_result['vehicles']:
                    qr_result = self.qr_generator.generate_qr_code(
                        vehicle['vin'],
                        dealership_name
                    )
                    qr_results.append(qr_result)
                
                job_result['qr_codes_generated'] = sum(1 for r in qr_results if r['success'])
            
            return job_result
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_complete_workflow(self, dealership_name: str) -> Dict:
        """Run complete workflow: Scrape -> Import -> Process -> Export"""
        try:
            logger.info(f"Starting complete workflow for {dealership_name}")
            
            # Step 1: Run scraper
            scraper_result = self.run_scraper_and_import(dealership_name)
            if not scraper_result['success']:
                return scraper_result
            
            # Step 2: Create order and export
            order_result = self.create_order_and_export(dealership_name)
            
            # Combine results
            return {
                'success': True,
                'dealership': dealership_name,
                'vehicles_scraped': scraper_result['vehicles_scraped'],
                'vehicles_imported': scraper_result['vehicles_imported'],
                'export_file': order_result.get('export_file'),
                'qr_codes_generated': order_result.get('qr_codes_generated', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        try:
            # Get database stats
            stats = self.db.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM raw_vehicle_data) as raw_count,
                    (SELECT COUNT(*) FROM normalized_vehicle_data) as normalized_count,
                    (SELECT COUNT(DISTINCT location) FROM normalized_vehicle_data) as dealership_count,
                    (SELECT COUNT(*) FROM order_processing_jobs WHERE status = 'completed') as completed_jobs,
                    (SELECT COUNT(*) FROM qr_file_tracking WHERE file_exists = true) as qr_files
            """)[0]
            
            # Get dealership status
            dealership_status = self.db.execute_query("""
                SELECT 
                    dc.name,
                    COUNT(nvd.id) as vehicle_count,
                    MAX(nvd.last_seen_date) as last_update
                FROM dealership_configs dc
                LEFT JOIN normalized_vehicle_data nvd ON dc.name = nvd.location
                WHERE dc.is_active = true
                GROUP BY dc.name
                ORDER BY dc.name
            """)
            
            return {
                'success': True,
                'database_stats': stats,
                'dealerships': dealership_status,
                'database_connected': self.db.test_connection()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Test the integration"""
    bridge = ScraperDatabaseBridge()
    
    # Get system status
    print("Checking system status...")
    status = bridge.get_system_status()
    
    if status['success']:
        print(f"Database connected: {status['database_connected']}")
        print(f"Total vehicles in database: {status['database_stats']['normalized_count']}")
        print(f"Active dealerships: {status['database_stats']['dealership_count']}")
        
        # Test with a known working scraper
        test_dealership = "BMW of West St. Louis"
        print(f"\nTesting workflow with {test_dealership}...")
        
        result = bridge.run_complete_workflow(test_dealership)
        
        if result['success']:
            print(f"Success! Scraped {result['vehicles_scraped']} vehicles")
            print(f"Imported {result['vehicles_imported']} to database")
            print(f"Export file: {result['export_file']}")
            print(f"QR codes generated: {result['qr_codes_generated']}")
        else:
            print(f"Error: {result['error']}")
    else:
        print(f"System check failed: {status['error']}")

if __name__ == "__main__":
    main()