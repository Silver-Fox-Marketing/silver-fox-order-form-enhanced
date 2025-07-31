#!/usr/bin/env python3
"""
Silver Fox Scraper Import Integration
====================================
Imports existing scrapers into the integrated database system
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add paths for both systems
sys.path.append(os.path.join(os.path.dirname(__file__), 'silverfox_scraper_system/silverfox_system'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/scripts'))

# Import from database system
from database_connection import db_manager
from order_processing_integration import OrderProcessingIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScraperImportIntegrator:
    """Integrates existing scrapers with the database system"""
    
    def __init__(self):
        self.db = db_manager
        self.scraper_base_path = Path("silverfox_scraper_system/silverfox_system")
        self.config_path = self.scraper_base_path / "config"
        self.scrapers_path = self.scraper_base_path / "core/scrapers/dealerships"
        
        # Confirmed working scrapers from CLAUDE.md
        self.confirmed_working = [
            "BMW of West St. Louis",
            "Suntrup Ford West", 
            "Suntrup Ford Kirkwood",
            "Joe Machens Hyundai",
            "Joe Machens Toyota",
            "Columbia Honda",
            "Dave Sinclair Lincoln South",
            "Thoroughbred Ford"
        ]
        
        # Ranch Mirage scrapers (need constructor fixes)
        self.ranch_mirage_scrapers = [
            "Jaguar Ranch Mirage",
            "Land Rover Ranch Mirage", 
            "Aston Martin Ranch Mirage",
            "Bentley Ranch Mirage",
            "McLaren Ranch Mirage",
            "Rolls-Royce Ranch Mirage"
        ]
        
        # Name mapping from friendly names to config file names
        self.name_mapping = {
            "BMW of West St. Louis": "bmwofweststlouis",
            "Suntrup Ford West": "suntrupfordwest",
            "Suntrup Ford Kirkwood": "suntrupfordkirkwood", 
            "Joe Machens Hyundai": "joemachenshyundai",
            "Joe Machens Toyota": "joemachenstoyota",
            "Columbia Honda": "columbiahonda",
            "Dave Sinclair Lincoln South": "davesinclairlincolnsouth",
            "Thoroughbred Ford": "thoroughbredford"
        }
    
    def load_scraper_config(self, config_name: str) -> Optional[Dict]:
        """Load a scraper configuration file"""
        try:
            config_file = self.config_path / f"{config_name}.json"
            if not config_file.exists():
                logger.error(f"Config file not found: {config_file}")
                return None
                
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded config for {config.get('name', config_name)}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            return None
    
    def update_database_dealership_config(self, dealership_name: str, config: Dict) -> bool:
        """Update or insert dealership configuration in database"""
        try:
            # Extract filtering and output rules from scraper config
            filtering_rules = {}
            output_rules = {}
            
            if 'filtering_rules' in config:
                filtering_rules = config['filtering_rules']
            
            if 'extraction_config' in config:
                output_rules = {
                    'fields': config['extraction_config'].get('data_fields', []),
                    'sort_by': ['make', 'model', 'year']
                }
            
            # Create QR output path
            qr_path = f"C:/qr_codes/{config.get('id', dealership_name.lower().replace(' ', '_'))}"
            
            # Upsert dealership configuration
            self.db.execute_non_query("""
                INSERT INTO dealership_configs (name, filtering_rules, output_rules, qr_output_path, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    filtering_rules = EXCLUDED.filtering_rules,
                    output_rules = EXCLUDED.output_rules,  
                    qr_output_path = EXCLUDED.qr_output_path,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                dealership_name,
                json.dumps(filtering_rules),
                json.dumps(output_rules),
                qr_path,
                True
            ))
            
            logger.info(f"Updated database config for {dealership_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating database config for {dealership_name}: {e}")
            return False
    
    def test_scraper_import(self, config_name: str, dealership_name: str) -> Dict:
        """Test importing a scraper and running it"""
        try:
            logger.info(f"Testing scraper import for {dealership_name}")
            
            # Try to import the working version of the scraper
            scraper_module = None
            module_variations = [
                f"{config_name}_working",
                f"{config_name}_optimized", 
                f"{config_name}_production"
            ]
            
            for variation in module_variations:
                try:
                    # Dynamically import the scraper module
                    module_path = f"core.scrapers.dealerships.{variation}"
                    
                    # Add the scraper system to path
                    scraper_sys_path = str(Path("silverfox_scraper_system/silverfox_system").absolute())
                    if scraper_sys_path not in sys.path:
                        sys.path.insert(0, scraper_sys_path)
                    
                    scraper_module = __import__(module_path, fromlist=[''])
                    logger.info(f"Successfully imported {variation}")
                    break
                    
                except ImportError as e:
                    logger.debug(f"Could not import {variation}: {e}")
                    continue
            
            if not scraper_module:
                return {
                    'success': False,
                    'error': f'No working scraper module found for {config_name}',
                    'dealership': dealership_name
                }
            
            # Try to find the scraper class
            scraper_class = None
            class_variations = [
                f"{config_name.title().replace('_', '')}WorkingScraper",
                f"{config_name.title().replace('_', '')}OptimizedScraper",
                f"{config_name.title().replace('_', '')}ProductionScraper",
                f"{config_name.title().replace('_', '')}Scraper",
                # Handle specific class name patterns
                "BmwOfWestStLouisOptimizedScraper",
                "SuntrupFordWestOptimizedScraper"
            ]
            
            for class_name in class_variations:
                if hasattr(scraper_module, class_name):
                    scraper_class = getattr(scraper_module, class_name)
                    logger.info(f"Found scraper class: {class_name}")
                    break
            
            if not scraper_class:
                return {
                    'success': False,
                    'error': f'No scraper class found in module for {config_name}',
                    'dealership': dealership_name
                }
            
            # Test instantiation
            try:
                scraper_instance = scraper_class()
                logger.info(f"Successfully instantiated scraper for {dealership_name}")
                
                return {
                    'success': True,
                    'dealership': dealership_name,
                    'module': module_path,
                    'class': scraper_class.__name__,
                    'scraper_ready': True
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Scraper instantiation failed: {str(e)}',
                    'dealership': dealership_name,
                    'module': module_path,
                    'class': scraper_class.__name__ if scraper_class else 'Unknown'
                }
            
        except Exception as e:
            logger.error(f"Error testing scraper import for {dealership_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'dealership': dealership_name
            }
    
    def import_working_scrapers(self) -> Dict:
        """Import all confirmed working scrapers"""
        results = {
            'successful_imports': [],
            'failed_imports': [],
            'database_updates': [],
            'total_processed': 0
        }
        
        logger.info("Starting import of confirmed working scrapers")
        
        for dealership_name in self.confirmed_working:
            results['total_processed'] += 1
            
            # Get config name
            config_name = self.name_mapping.get(dealership_name, 
                                               dealership_name.lower().replace(' ', '').replace('.', ''))
            
            # Load scraper configuration
            config = self.load_scraper_config(config_name)
            if not config:
                results['failed_imports'].append({
                    'dealership': dealership_name,
                    'error': 'Config file not found'
                })
                continue
            
            # Update database configuration
            db_success = self.update_database_dealership_config(dealership_name, config)
            if db_success:
                results['database_updates'].append(dealership_name)
            
            # Test scraper import
            import_result = self.test_scraper_import(config_name, dealership_name)
            
            if import_result['success']:
                results['successful_imports'].append(import_result)
                logger.info(f"Successfully integrated {dealership_name}")
            else:
                results['failed_imports'].append(import_result)
                logger.error(f"Failed to integrate {dealership_name}: {import_result['error']}")
        
        return results
    
    def create_scraper_registry(self, results: Dict) -> None:
        """Create a registry of all imported scrapers"""
        registry = {
            'created_at': datetime.now().isoformat(),
            'total_scrapers': len(self.confirmed_working),
            'successful_imports': len(results['successful_imports']),
            'failed_imports': len(results['failed_imports']),
            'scrapers': {}
        }
        
        # Add successful scrapers
        for scraper_info in results['successful_imports']:
            dealership = scraper_info['dealership']
            config_name = self.name_mapping.get(dealership, 
                                               dealership.lower().replace(' ', '').replace('.', ''))
            
            registry['scrapers'][dealership] = {
                'status': 'active',
                'config_name': config_name,
                'module_path': scraper_info.get('module'),
                'class_name': scraper_info.get('class'),
                'last_tested': datetime.now().isoformat()
            }
        
        # Add failed scrapers
        for scraper_info in results['failed_imports']:
            dealership = scraper_info['dealership']
            registry['scrapers'][dealership] = {
                'status': 'failed',
                'error': scraper_info['error'],
                'last_tested': datetime.now().isoformat()
            }
        
        # Save registry
        registry_file = Path("scraper_integration_registry.json")
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"Created scraper registry: {registry_file}")

def main():
    """Main import process"""
    print("=" * 60)
    print("SILVER FOX SCRAPER IMPORT INTEGRATION")  
    print("=" * 60)
    
    integrator = ScraperImportIntegrator()
    
    # Test database connection
    if not integrator.db.test_connection():
        print("ERROR: Database connection failed")
        return False
    
    print("OK Database connection verified")
    
    # Import working scrapers
    print(f"\nImporting {len(integrator.confirmed_working)} confirmed working scrapers...")
    results = integrator.import_working_scrapers()
    
    # Create registry
    integrator.create_scraper_registry(results)
    
    # Print summary
    print(f"\n" + "=" * 60)
    print("SCRAPER IMPORT SUMMARY")
    print("=" * 60)
    
    print(f"Total processed: {results['total_processed']}")
    print(f"Successful imports: {len(results['successful_imports'])}")
    print(f"Failed imports: {len(results['failed_imports'])}")
    print(f"Database configs updated: {len(results['database_updates'])}")
    
    if results['successful_imports']:
        print(f"\nSuccessful imports:")
        for scraper in results['successful_imports']:
            print(f"  - {scraper['dealership']}: {scraper['class']}")
    
    if results['failed_imports']:
        print(f"\nFailed imports:")
        for scraper in results['failed_imports']:
            print(f"  - {scraper['dealership']}: {scraper['error']}")
    
    success_rate = (len(results['successful_imports']) / results['total_processed']) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("OK Scraper integration successful!")
        return True
    else:
        print("WARNING Some scrapers failed to import")
        return False

if __name__ == "__main__":
    main()