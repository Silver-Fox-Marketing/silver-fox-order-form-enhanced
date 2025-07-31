#!/usr/bin/env python3
"""
Real Scraper Testing System
===========================

Test the real working scrapers to verify they can extract actual data
from dealership APIs instead of just generating fallback data.

Author: Silver Fox Assistant
Created: 2025-07-28
"""

import sys
import os
import logging
import importlib.util
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealScraperTester:
    """Test real working scrapers"""
    
    def __init__(self):
        self.scrapers_path = Path("silverfox_scraper_system/silverfox_system/core/scrapers/dealerships")
        self.test_results = []
    
    def load_scraper_module(self, scraper_file: Path):
        """Dynamically load a scraper module"""
        try:
            spec = importlib.util.spec_from_file_location("scraper_module", scraper_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            logger.error(f"Error loading {scraper_file}: {e}")
            return None
    
    def test_scraper(self, scraper_name: str, scraper_file: Path):
        """Test a specific scraper"""
        logger.info(f"Testing scraper: {scraper_name}")
        
        try:
            # Load the scraper module
            module = self.load_scraper_module(scraper_file)
            if not module:
                return False
            
            # Find the scraper class (look for classes ending with 'Scraper')
            scraper_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name.endswith('Scraper'):
                    scraper_class = attr
                    break
            
            if not scraper_class:
                logger.error(f"No scraper class found in {scraper_name}")
                return False
            
            # Initialize and test the scraper
            scraper = scraper_class()
            logger.info(f"Initialized {scraper_class.__name__}")
            
            # Run the scraper
            start_time = datetime.now()
            vehicles = scraper.get_all_vehicles()
            end_time = datetime.now()
            
            # Analyze results
            duration = (end_time - start_time).total_seconds()
            vehicle_count = len(vehicles) if vehicles else 0
            
            if vehicles:
                # Check data source to see if it's real data or fallback
                first_vehicle = vehicles[0]
                data_source = first_vehicle.get('data_source', 'unknown')
                is_real_data = 'real' in data_source.lower()
                
                test_result = {
                    'scraper_name': scraper_name,
                    'success': True,
                    'vehicle_count': vehicle_count,
                    'duration_seconds': duration,
                    'data_source': data_source,
                    'is_real_data': is_real_data,
                    'sample_vehicle': {
                        'year': first_vehicle.get('year'),
                        'make': first_vehicle.get('make'),
                        'model': first_vehicle.get('model'),
                        'vin': first_vehicle.get('vin', '')[:10] + '...',  # Truncate VIN for privacy
                        'price': first_vehicle.get('price')
                    }
                }
                
                logger.info(f"SUCCESS: {scraper_name} returned {vehicle_count} vehicles in {duration:.1f}s")
                logger.info(f"Data source: {data_source}")
                if is_real_data:
                    logger.info("🎉 REAL DATA EXTRACTED!")
                else:
                    logger.warning("⚠️ Using fallback data")
                
            else:
                test_result = {
                    'scraper_name': scraper_name,
                    'success': False,
                    'vehicle_count': 0,
                    'duration_seconds': duration,
                    'data_source': 'failed',
                    'is_real_data': False,
                    'error': 'No vehicles returned'
                }
                logger.error(f"FAILED: {scraper_name} returned no vehicles")
            
            self.test_results.append(test_result)
            return test_result['success']
            
        except Exception as e:
            logger.error(f"Error testing {scraper_name}: {e}")
            test_result = {
                'scraper_name': scraper_name,
                'success': False,
                'vehicle_count': 0,
                'duration_seconds': 0,
                'data_source': 'error',
                'is_real_data': False,
                'error': str(e)
            }
            self.test_results.append(test_result)
            return False
    
    def test_all_real_scrapers(self):
        """Test all real working scrapers"""
        logger.info("Starting real scraper testing")
        
        # Find all real working scrapers
        real_scrapers = list(self.scrapers_path.glob("*_real_working.py"))
        
        if not real_scrapers:
            logger.error("No real working scrapers found!")
            return
        
        logger.info(f"Found {len(real_scrapers)} real working scrapers to test")
        
        success_count = 0
        real_data_count = 0
        
        for scraper_file in real_scrapers:
            scraper_name = scraper_file.stem
            success = self.test_scraper(scraper_name, scraper_file)
            
            if success:
                success_count += 1
                # Check if this scraper got real data
                last_result = self.test_results[-1]
                if last_result.get('is_real_data', False):
                    real_data_count += 1
            
            logger.info("-" * 60)
        
        # Generate summary report
        self.generate_summary_report(len(real_scrapers), success_count, real_data_count)
    
    def generate_summary_report(self, total_scrapers: int, success_count: int, real_data_count: int):
        """Generate and display summary report"""
        logger.info("=" * 80)
        logger.info("REAL SCRAPER TESTING SUMMARY REPORT")
        logger.info("=" * 80)
        
        logger.info(f"Total scrapers tested: {total_scrapers}")
        logger.info(f"Successful scrapers: {success_count} ({success_count/total_scrapers*100:.1f}%)")
        logger.info(f"Real data scrapers: {real_data_count} ({real_data_count/total_scrapers*100:.1f}%)")
        logger.info(f"Fallback data scrapers: {success_count - real_data_count}")
        logger.info(f"Failed scrapers: {total_scrapers - success_count}")
        
        logger.info("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            data_type = "🎯 REAL" if result.get('is_real_data', False) else "🔄 FALLBACK"
            
            logger.info(f"{status} {data_type} | {result['scraper_name']} ({result['vehicle_count']} vehicles)")
            
            if result['success'] and result.get('sample_vehicle'):
                sample = result['sample_vehicle']
                logger.info(f"    Sample: {sample['year']} {sample['make']} {sample['model']} | VIN: {sample['vin']} | Price: ${sample['price']}")
        
        # Determine overall success
        if real_data_count > 0:
            logger.info("\n🎉 SUCCESS: At least one scraper is extracting real data!")
            if real_data_count == total_scrapers:
                logger.info("🏆 PERFECT: All scrapers are extracting real data!")
            else:
                logger.info(f"📈 PROGRESS: {real_data_count}/{total_scrapers} scrapers extracting real data")
        else:
            logger.warning("\n⚠️ WARNING: No scrapers are extracting real data - all using fallback")
        
        logger.info("=" * 80)

def main():
    """Main testing process"""
    print("=" * 80)
    print("TESTING REAL WORKING SCRAPERS")
    print("=" * 80)
    
    tester = RealScraperTester()
    tester.test_all_real_scrapers()

if __name__ == "__main__":
    main()