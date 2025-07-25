#!/usr/bin/env python3
"""
Ranch Mirage Optimization Test Suite
Comprehensive testing for all 6 indiGO Auto Group luxury dealership scrapers
Tests optimization framework integration and scraper functionality
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

# Import all Ranch Mirage scrapers
try:
    from jaguarranchomirage_working import JaguarRanchoMirageWorkingScraper
    from landroverranchomirage_working import LandRoverRanchoMirageWorkingScraper
    from astonmartinranchomirage_working import AstonMartinRanchoMirageWorkingScraper
    from bentleyranchomirage_working import BentleyRanchoMirageWorkingScraper
    from mclarenranchomirage_working import McLarenRanchoMirageWorkingScraper
    from rollsroyceranchomirage_working import RollsRoyceRanchoMirageWorkingScraper
except ImportError as e:
    print(f"❌ Error importing scrapers: {e}")
    sys.exit(1)

class RanchMirageTestSuite:
    """Comprehensive test suite for Ranch Mirage scrapers"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.results = {}
        self.test_start_time = datetime.now()
        
        # Dealership configurations
        self.dealership_configs = {
            'jaguar': {
                'id': 'jaguarranchomirage',
                'name': 'Jaguar Rancho Mirage',
                'base_url': 'https://www.jaguarranchomirage.com',
                'scraper_class': JaguarRanchoMirageWorkingScraper,
                'type': 'luxury',
                'expected_models': ['F-PACE', 'E-PACE', 'I-PACE', 'XE', 'XF', 'XJ', 'F-TYPE']
            },
            'landrover': {
                'id': 'landroverranchomirage',
                'name': 'Land Rover Rancho Mirage',
                'base_url': 'https://www.landroverofranchomirage.com',
                'scraper_class': LandRoverRanchoMirageWorkingScraper,
                'type': 'luxury',
                'expected_models': ['Range Rover', 'Range Rover Sport', 'Range Rover Evoque', 'Discovery', 'Defender']
            },
            'astonmartin': {
                'id': 'astonmartinranchomirage',
                'name': 'Aston Martin Rancho Mirage',
                'base_url': 'https://www.astonmartinranchomirage.com',
                'scraper_class': AstonMartinRanchoMirageWorkingScraper,
                'type': 'luxury',
                'expected_models': ['DB11', 'DBS', 'Vantage', 'DBX']
            },
            'bentley': {
                'id': 'bentleyranchomirage',
                'name': 'Bentley Rancho Mirage',
                'base_url': 'https://www.bentleyofranchomirage.com',
                'scraper_class': BentleyRanchoMirageWorkingScraper,
                'type': 'luxury',
                'expected_models': ['Continental GT', 'Continental GTC', 'Flying Spur', 'Bentayga']
            },
            'mclaren': {
                'id': 'mclarenranchomirage',
                'name': 'McLaren Rancho Mirage',
                'base_url': 'https://www.mclarenranchomirage.com',
                'scraper_class': McLarenRanchoMirageWorkingScraper,
                'type': 'supercar',
                'expected_models': ['570S', '720S', 'Artura', 'GT']
            },
            'rollsroyce': {
                'id': 'rollsroyceranchomirage',
                'name': 'Rolls-Royce Motor Cars Rancho Mirage',
                'base_url': 'https://www.rolls-roycemotorcarsranchomirage.com',
                'scraper_class': RollsRoyceRanchoMirageWorkingScraper,
                'type': 'ultra_luxury',
                'expected_models': ['Ghost', 'Phantom', 'Wraith', 'Dawn', 'Cullinan']
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for test suite"""
        logger = logging.getLogger('RanchMirageTestSuite')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        log_filename = f"ranch_mirage_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_test_config(self, dealership_type: str):
        """Create test configuration based on dealership type"""
        
        class TestConfig:
            def __init__(self, dealership_type: str):
                if dealership_type == "ultra_luxury":
                    self.request_delay = 8.0
                    self.timeout = 120
                elif dealership_type == "supercar":
                    self.request_delay = 6.0
                    self.timeout = 90
                else:  # luxury
                    self.request_delay = 4.0
                    self.timeout = 60
        
        return TestConfig(dealership_type)
    
    def test_scraper_initialization(self, dealership_key: str, config: Dict[str, Any]) -> bool:
        """Test scraper initialization and optimization framework"""
        
        self.logger.info(f"🔧 Testing {config['name']} initialization...")
        
        try:
            scraper_config = self._create_test_config(config['type'])
            scraper = config['scraper_class'](config, scraper_config)
            
            # Test optimization framework initialization
            if hasattr(scraper, 'optimizer'):
                self.logger.info(f"✅ Optimization framework initialized for {config['name']}")
                
                # Test user agent rotation
                if hasattr(scraper.optimizer, 'user_agent_manager'):
                    agent1 = scraper.optimizer.user_agent_manager.get_rotating_agent()
                    agent2 = scraper.optimizer.user_agent_manager.get_rotating_agent()
                    if agent1 and agent2:
                        self.logger.info(f"✅ User agent rotation working for {config['name']}")
                    else:
                        self.logger.warning(f"⚠️ User agent rotation issue for {config['name']}")
                
                # Test timing patterns
                if hasattr(scraper.optimizer, 'timing'):
                    delay = scraper.optimizer.timing.get_request_delay()
                    if delay > 0:
                        self.logger.info(f"✅ Timing patterns working for {config['name']} (delay: {delay:.2f}s)")
                    else:
                        self.logger.warning(f"⚠️ Timing pattern issue for {config['name']}")
                
                return True
            else:
                self.logger.error(f"❌ No optimization framework found for {config['name']}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Initialization failed for {config['name']}: {str(e)}")
            return False
    
    def test_scraper_functionality(self, dealership_key: str, config: Dict[str, Any], quick_test: bool = True) -> Dict[str, Any]:
        """Test scraper functionality with optimization"""
        
        self.logger.info(f"🧪 Testing {config['name']} scraper functionality...")
        
        test_result = {
            'dealership': config['name'],
            'success': False,
            'vehicles_found': 0,
            'api_success': False,
            'chrome_fallback': False,
            'optimization_used': False,
            'execution_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            scraper_config = self._create_test_config(config['type'])
            scraper = config['scraper_class'](config, scraper_config)
            
            if hasattr(scraper, 'optimizer'):
                test_result['optimization_used'] = True
            
            # Test inventory scraping (limited for testing)
            if quick_test:
                # Override some limits for quick testing
                original_max_pages = getattr(scraper, 'max_pages', None)
                if hasattr(scraper, '_scrape_with_api'):
                    # Limit API testing to 1-2 pages for speed
                    self.logger.info(f"Running quick API test for {config['name']}...")
            
            vehicles = scraper.scrape_inventory()
            
            test_result['vehicles_found'] = len(vehicles)
            test_result['success'] = len(vehicles) > 0
            
            if vehicles:
                # Validate sample vehicle data
                sample_vehicle = vehicles[0]
                required_fields = ['vin', 'year', 'make', 'model', 'dealer_name']
                missing_fields = [field for field in required_fields if not sample_vehicle.get(field)]
                
                if missing_fields:
                    test_result['errors'].append(f"Missing required fields: {missing_fields}")
                    self.logger.warning(f"⚠️ Missing fields in {config['name']}: {missing_fields}")
                else:
                    self.logger.info(f"✅ Vehicle data validation passed for {config['name']}")
                
                # Check for expected models
                found_models = set(v.get('model', '') for v in vehicles if v.get('model'))
                expected_models = set(config['expected_models'])
                matching_models = found_models.intersection(expected_models)
                
                if matching_models:
                    self.logger.info(f"✅ Found expected models for {config['name']}: {list(matching_models)}")
                else:
                    self.logger.warning(f"⚠️ No expected models found for {config['name']}")
                    self.logger.info(f"   Found models: {list(found_models)}")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ Scraper test failed for {config['name']}: {str(e)}")
        
        test_result['execution_time'] = time.time() - start_time
        
        return test_result
    
    def run_comprehensive_test(self, quick_test: bool = True, specific_dealerships: List[str] = None) -> None:
        """Run comprehensive test suite for all or specific dealerships"""
        
        self.logger.info("🚀 Starting Ranch Mirage Optimization Test Suite")
        self.logger.info(f"Test type: {'Quick' if quick_test else 'Full'}")
        
        if specific_dealerships:
            dealerships_to_test = {k: v for k, v in self.dealership_configs.items() if k in specific_dealerships}
        else:
            dealerships_to_test = self.dealership_configs
        
        total_dealerships = len(dealerships_to_test)
        successful_tests = 0
        
        for dealership_key, config in dealerships_to_test.items():
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Testing {config['name']} ({config['type']})")
            self.logger.info(f"{'='*60}")
            
            # Test 1: Initialization
            init_success = self.test_scraper_initialization(dealership_key, config)
            
            # Test 2: Functionality
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
        """Generate comprehensive test summary"""
        
        test_duration = datetime.now() - self.test_start_time
        success_rate = (successful_tests / total_dealerships) * 100 if total_dealerships > 0 else 0
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("🏁 RANCH MIRAGE OPTIMIZATION TEST SUMMARY")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Total dealerships tested: {total_dealerships}")
        self.logger.info(f"Successful tests: {successful_tests}")
        self.logger.info(f"Failed tests: {total_dealerships - successful_tests}")
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"Total test duration: {test_duration}")
        
        self.logger.info(f"\n📊 DETAILED RESULTS:")
        for dealership_key, result in self.results.items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            vehicles = result.get('vehicles_found', 0)
            time_taken = result.get('execution_time', 0)
            optimization = "🔧 Optimized" if result.get('optimization_used') else "⚠️ Basic"
            
            self.logger.info(f"  {status} {result['dealership']}: {vehicles} vehicles in {time_taken:.1f}s {optimization}")
            
            if result.get('errors'):
                for error in result['errors']:
                    self.logger.info(f"    ⚠️ {error}")
        
        # Optimization framework stats
        optimized_count = sum(1 for r in self.results.values() if r.get('optimization_used'))
        self.logger.info(f"\n🔧 OPTIMIZATION FRAMEWORK USAGE:")
        self.logger.info(f"  Scrapers using optimization: {optimized_count}/{len(self.results)}")
        
        if success_rate >= 80:
            self.logger.info(f"\n🎉 EXCELLENT! Ranch Mirage optimization system is performing well!")
        elif success_rate >= 60:
            self.logger.info(f"\n👍 GOOD! Most scrapers are working with optimization.")
        else:
            self.logger.info(f"\n⚠️ NEEDS ATTENTION! Multiple scrapers need debugging.")

def main():
    """Main test execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Ranch Mirage Scraper Optimization Test Suite')
    parser.add_argument('--full', action='store_true', help='Run full test (slower)')
    parser.add_argument('--dealerships', nargs='+', 
                       choices=['jaguar', 'landrover', 'astonmartin', 'bentley', 'mclaren', 'rollsroyce'],
                       help='Test specific dealerships only')
    
    args = parser.parse_args()
    
    test_suite = RanchMirageTestSuite()
    
    quick_test = not args.full
    specific_dealerships = args.dealerships
    
    test_suite.run_comprehensive_test(quick_test=quick_test, specific_dealerships=specific_dealerships)

if __name__ == "__main__":
    main()