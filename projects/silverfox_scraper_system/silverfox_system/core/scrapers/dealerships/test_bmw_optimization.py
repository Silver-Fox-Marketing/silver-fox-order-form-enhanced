#!/usr/bin/env python3
"""
BMW Optimization Test Suite
Tests BMW-specific optimization framework integration and scraper functionality
Extends Ranch Mirage testing approach for BMW dealerships
"""

import sys
import os
import logging
import time
from typing import Dict, List, Any
from datetime import datetime

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(parent_dir, 'utils')
base_dir = os.path.join(parent_dir, 'base')
sys.path.append(parent_dir)
sys.path.append(utils_dir)
sys.path.append(base_dir)

# Import BMW scrapers
try:
    from bmwofweststlouis_working import BMWofWestStLouisWorkingScraper
except ImportError as e:
    print(f"❌ Error importing BMW scrapers: {e}")
    sys.exit(1)

# Import BMW optimization framework
try:
    from bmw_optimization_framework import (
        BMWOptimizationFramework,
        create_bmw_west_st_louis_optimizer,
        create_bmw_optimizer
    )
except ImportError as e:
    print(f"❌ Error importing BMW optimization framework: {e}")
    sys.exit(1)

class BMWTestSuite:
    """Comprehensive test suite for BMW optimization framework and scrapers"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.results = {}
        self.test_start_time = datetime.now()
        
        # BMW dealership configurations
        self.bmw_configs = {
            'bmw_west_st_louis': {
                'id': 'bmwofweststlouis',
                'name': 'BMW of West St Louis',
                'base_url': 'https://www.bmwofweststlouis.com',
                'scraper_class': BMWofWestStLouisWorkingScraper,
                'type': 'luxury',
                'api_type': 'algolia',
                'expected_models': ['3 Series', '4 Series', '5 Series', 'X3', 'X5', 'X7', 'i4', 'iX'],
                'expected_vehicle_types': ['new', 'used', 'certified']
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for BMW test suite"""
        logger = logging.getLogger('BMWTestSuite')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        log_filename = f"bmw_optimization_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_test_config(self, dealership_type: str):
        """Create test configuration based on BMW dealership type"""
        
        class TestConfig:
            def __init__(self, dealership_type: str):
                if dealership_type == "ultra_luxury":  # BMW M-Series specialists
                    self.request_delay = 6.0
                    self.timeout = 90
                elif dealership_type == "supercar":  # Premium BMW dealerships
                    self.request_delay = 4.0
                    self.timeout = 60
                else:  # Standard BMW luxury dealerships
                    self.request_delay = 3.0
                    self.timeout = 45
        
        return TestConfig(dealership_type)
    
    def test_bmw_optimization_framework(self) -> bool:
        """Test BMW optimization framework initialization and components"""
        
        self.logger.info("🔧 Testing BMW Optimization Framework...")
        
        try:
            # Test framework creation
            optimizer = create_bmw_west_st_louis_optimizer()
            
            # Test user agent management
            agent1 = optimizer.user_agent_manager.get_rotating_agent()
            agent2 = optimizer.user_agent_manager.get_bmw_optimized_agent()
            
            if agent1 and agent2:
                self.logger.info("✅ BMW user agent rotation working")
            else:
                self.logger.error("❌ BMW user agent rotation failed")
                return False
            
            # Test timing patterns
            algolia_delay = optimizer.timing.get_algolia_request_delay()
            vehicle_type_delay = optimizer.timing.get_vehicle_type_delay()
            
            if algolia_delay > 0 and vehicle_type_delay > 0:
                self.logger.info(f"✅ BMW timing patterns working (Algolia: {algolia_delay:.2f}s, VehicleType: {vehicle_type_delay:.2f}s)")
            else:
                self.logger.error("❌ BMW timing patterns failed")
                return False
            
            # Test BMW headers
            headers = optimizer.get_bmw_headers()
            required_headers = ['User-Agent', 'Accept', 'Content-Type']
            
            if all(header in headers for header in required_headers):
                self.logger.info("✅ BMW headers generation working")
            else:
                self.logger.error("❌ BMW headers generation failed")
                return False
            
            self.logger.info("✅ BMW Optimization Framework test PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ BMW Optimization Framework test FAILED: {str(e)}")
            return False
    
    def test_scraper_initialization(self, dealership_key: str, config: Dict[str, Any]) -> bool:
        """Test BMW scraper initialization with optimization framework"""
        
        self.logger.info(f"🔧 Testing {config['name']} initialization...")
        
        try:
            scraper_config = self._create_test_config(config['type'])
            scraper = config['scraper_class'](config, scraper_config)
            
            # Test optimization framework integration
            if hasattr(scraper, 'optimizer'):
                self.logger.info(f"✅ BMW optimization framework integrated in {config['name']}")
                
                # Test BMW-specific methods
                if hasattr(scraper.optimizer, 'apply_algolia_optimization'):
                    self.logger.info(f"✅ Algolia optimization available for {config['name']}")
                else:
                    self.logger.warning(f"⚠️ Algolia optimization missing for {config['name']}")
                
                # Test BMW headers
                if hasattr(scraper, 'headers') and 'User-Agent' in scraper.headers:
                    self.logger.info(f"✅ BMW headers configured for {config['name']}")
                else:
                    self.logger.warning(f"⚠️ BMW headers issue for {config['name']}")
                
                return True
            else:
                self.logger.error(f"❌ No BMW optimization framework found for {config['name']}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Initialization failed for {config['name']}: {str(e)}")
            return False
    
    def test_scraper_functionality(self, dealership_key: str, config: Dict[str, Any], quick_test: bool = True) -> Dict[str, Any]:
        """Test BMW scraper functionality with optimization"""
        
        self.logger.info(f"🧪 Testing {config['name']} scraper functionality...")
        
        test_result = {
            'dealership': config['name'],
            'success': False,
            'vehicles_found': 0,
            'api_success': False,
            'optimization_used': False,
            'algolia_queries': 0,
            'vehicle_types_scraped': 0,
            'execution_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            scraper_config = self._create_test_config(config['type'])
            scraper = config['scraper_class'](config, scraper_config)
            
            if hasattr(scraper, 'optimizer'):
                test_result['optimization_used'] = True
            
            # Test Algolia API functionality (limited for testing)
            if quick_test and config.get('api_type') == 'algolia':
                self.logger.info(f"Testing Algolia API for {config['name']}...")
                
                # Test one vehicle type to verify API connectivity
                try:
                    test_vehicles = scraper._scrape_vehicle_type_api('used')
                    test_result['api_success'] = len(test_vehicles) > 0
                    test_result['vehicles_found'] = len(test_vehicles)
                    
                    if test_vehicles:
                        self.logger.info(f"✅ Algolia API test successful: {len(test_vehicles)} vehicles")
                    else:
                        self.logger.warning(f"⚠️ Algolia API returned no vehicles for {config['name']}")
                        
                except Exception as e:
                    test_result['errors'].append(f"Algolia API test failed: {str(e)}")
                    self.logger.warning(f"⚠️ Algolia API test failed for {config['name']}: {str(e)}")
            
            else:
                # Full inventory test
                vehicles = scraper.scrape_inventory()
                test_result['vehicles_found'] = len(vehicles)
                test_result['api_success'] = len(vehicles) > 0
            
            test_result['success'] = test_result['vehicles_found'] > 0
            
            # Get optimization stats if available
            if hasattr(scraper, 'optimizer') and hasattr(scraper.optimizer, 'stats'):
                stats = scraper.optimizer.stats
                test_result['algolia_queries'] = stats.get('algolia_queries', 0)
                test_result['vehicle_types_scraped'] = stats.get('vehicle_type_switches', 0)
            
            # Validate BMW-specific data if vehicles found
            if test_result['vehicles_found'] > 0:
                vehicles = []
                if quick_test:
                    # Use test vehicles from API test
                    try:
                        vehicles = scraper._scrape_vehicle_type_api('used')[:5]  # Sample
                    except:
                        vehicles = []
                else:
                    vehicles = scraper.scrape_inventory()[:5]  # Sample
                
                if vehicles:
                    sample_vehicle = vehicles[0]
                    required_fields = ['vin', 'year', 'make', 'model', 'dealer_name']
                    missing_fields = [field for field in required_fields if not sample_vehicle.get(field)]
                    
                    if missing_fields:
                        test_result['errors'].append(f"Missing required fields: {missing_fields}")
                        self.logger.warning(f"⚠️ Missing fields in {config['name']}: {missing_fields}")
                    else:
                        self.logger.info(f"✅ BMW vehicle data validation passed for {config['name']}")
                    
                    # Check for BMW-specific models
                    found_models = set(v.get('model', '') for v in vehicles if v.get('model'))
                    expected_models = set(config['expected_models'])
                    matching_models = found_models.intersection(expected_models)
                    
                    if matching_models:
                        self.logger.info(f"✅ Found expected BMW models for {config['name']}: {list(matching_models)}")
                    else:
                        self.logger.warning(f"⚠️ No expected BMW models found for {config['name']}")
                        self.logger.info(f"   Found models: {list(found_models)}")
                    
                    # Verify BMW make
                    bmw_vehicles = [v for v in vehicles if v.get('make', '').upper() == 'BMW']
                    if bmw_vehicles:
                        self.logger.info(f"✅ BMW make verification passed: {len(bmw_vehicles)}/{len(vehicles)} vehicles")
                    else:
                        test_result['errors'].append("No vehicles with BMW make found")
                        self.logger.warning(f"⚠️ No BMW make vehicles found for {config['name']}")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ BMW scraper test failed for {config['name']}: {str(e)}")
        
        test_result['execution_time'] = time.time() - start_time
        
        return test_result
    
    def run_comprehensive_test(self, quick_test: bool = True, specific_dealerships: List[str] = None) -> None:
        """Run comprehensive test suite for BMW dealerships"""
        
        self.logger.info("🚀 Starting BMW Optimization Test Suite")
        self.logger.info(f"Test type: {'Quick' if quick_test else 'Full'}")
        
        # Test 1: BMW Optimization Framework
        framework_success = self.test_bmw_optimization_framework()
        
        if not framework_success:
            self.logger.error("❌ BMW Optimization Framework test failed - stopping tests")
            return
        
        # Test 2: BMW Dealership Scrapers
        if specific_dealerships:
            dealerships_to_test = {k: v for k, v in self.bmw_configs.items() if k in specific_dealerships}
        else:
            dealerships_to_test = self.bmw_configs
        
        total_dealerships = len(dealerships_to_test)
        successful_tests = 0
        
        for dealership_key, config in dealerships_to_test.items():
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Testing {config['name']} ({config['type']} BMW)")
            self.logger.info(f"{'='*60}")
            
            # Test initialization
            init_success = self.test_scraper_initialization(dealership_key, config)
            
            # Test functionality
            if init_success:
                func_result = self.test_scraper_functionality(dealership_key, config, quick_test)
                self.results[dealership_key] = func_result
                
                if func_result['success']:
                    successful_tests += 1
                    self.logger.info(f"✅ {config['name']} test PASSED - {func_result['vehicles_found']} vehicles found")
                else:
                    self.logger.error(f"❌ {config['name']} test FAILED")
            else:
                self.results[dealership_key] = {
                    'dealership': config['name'],
                    'success': False,
                    'error': 'Initialization failed'
                }
        
        # Generate test summary
        self._generate_test_summary(total_dealerships, successful_tests)
    
    def _generate_test_summary(self, total_dealerships: int, successful_tests: int) -> None:
        """Generate comprehensive BMW test summary"""
        
        test_duration = datetime.now() - self.test_start_time
        success_rate = (successful_tests / total_dealerships) * 100 if total_dealerships > 0 else 0
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("🏁 BMW OPTIMIZATION TEST SUMMARY")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Total BMW dealerships tested: {total_dealerships}")
        self.logger.info(f"Successful tests: {successful_tests}")
        self.logger.info(f"Failed tests: {total_dealerships - successful_tests}")
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"Total test duration: {test_duration}")
        
        self.logger.info(f"\n📊 DETAILED BMW RESULTS:")
        for dealership_key, result in self.results.items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            vehicles = result.get('vehicles_found', 0)
            time_taken = result.get('execution_time', 0)
            optimization = "🔧 BMW Optimized" if result.get('optimization_used') else "⚠️ Basic"
            algolia_queries = result.get('algolia_queries', 0)
            
            self.logger.info(f"  {status} {result['dealership']}: {vehicles} vehicles in {time_taken:.1f}s {optimization}")
            
            if algolia_queries > 0:
                self.logger.info(f"    📡 Algolia queries: {algolia_queries}")
            
            if result.get('errors'):
                for error in result['errors']:
                    self.logger.info(f"    ⚠️ {error}")
        
        # BMW optimization framework stats
        optimized_count = sum(1 for r in self.results.values() if r.get('optimization_used'))
        self.logger.info(f"\n🔧 BMW OPTIMIZATION FRAMEWORK USAGE:")
        self.logger.info(f"  BMW scrapers using optimization: {optimized_count}/{len(self.results)}")
        
        total_algolia_queries = sum(r.get('algolia_queries', 0) for r in self.results.values())
        if total_algolia_queries > 0:
            self.logger.info(f"  Total Algolia API queries: {total_algolia_queries}")
        
        if success_rate >= 80:
            self.logger.info(f"\n🎉 EXCELLENT! BMW optimization system is performing well!")
        elif success_rate >= 60:
            self.logger.info(f"\n👍 GOOD! Most BMW scrapers are working with optimization.")
        else:
            self.logger.info(f"\n⚠️ NEEDS ATTENTION! BMW scrapers need debugging.")

def main():
    """Main BMW test execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='BMW Optimization Test Suite')
    parser.add_argument('--full', action='store_true', help='Run full test (slower)')
    parser.add_argument('--dealerships', nargs='+', 
                       choices=['bmw_west_st_louis'],
                       help='Test specific BMW dealerships only')
    
    args = parser.parse_args()
    
    test_suite = BMWTestSuite()
    
    quick_test = not args.full
    specific_dealerships = args.dealerships
    
    test_suite.run_comprehensive_test(quick_test=quick_test, specific_dealerships=specific_dealerships)

if __name__ == "__main__":
    main()