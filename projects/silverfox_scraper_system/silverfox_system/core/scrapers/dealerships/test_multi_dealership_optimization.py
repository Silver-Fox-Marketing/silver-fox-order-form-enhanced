#!/usr/bin/env python3
"""
Multi-Dealership Optimization Test Suite
Comprehensive testing for all dealership groups with optimization frameworks
Tests Ranch Mirage luxury brands, BMW, Suntrup, and other dealership groups
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

# Import all enhanced scrapers
try:
    # Ranch Mirage luxury dealerships
    from jaguarranchomirage_working import JaguarRanchoMirageWorkingScraper
    from landroverranchomirage_working import LandRoverRanchoMirageWorkingScraper
    from astonmartinranchomirage_working import AstonMartinRanchoMirageWorkingScraper
    from bentleyranchomirage_working import BentleyRanchoMirageWorkingScraper
    from mclarenranchomirage_working import McLarenRanchoMirageWorkingScraper
    from rollsroyceranchomirage_working import RollsRoyceRanchoMirageWorkingScraper
    
    # BMW dealerships
    from bmwofweststlouis_working import BMWofWestStLouisWorkingScraper
    
    # Suntrup dealerships
    from suntrupfordwest_working import SuntrupFordWestWorkingScraper
    
except ImportError as e:
    print(f"❌ Error importing scrapers: {e}")
    sys.exit(1)

# Import optimization frameworks
try:
    from multi_dealership_optimization_framework import (
        MultiDealershipOptimizationFramework,
        DealershipGroup,
        DealershipTier,
        DealershipPlatform,
        create_ranch_mirage_optimizer,
        create_bmw_optimizer,
        create_suntrup_optimizer,
        detect_and_create_optimizer
    )
    from bmw_optimization_framework import BMWOptimizationFramework
    from ranch_mirage_antibot_utils import RanchMirageOptimizationFramework
except ImportError as e:
    print(f"❌ Error importing optimization frameworks: {e}")
    sys.exit(1)

class MultiDealershipTestSuite:
    """Comprehensive test suite for all dealership optimization frameworks"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.results = {}
        self.test_start_time = datetime.now()
        
        # All dealership configurations organized by group
        self.dealership_configs = {
            # Ranch Mirage Luxury Group
            'ranch_mirage': {
                'jaguar': {
                    'id': 'jaguarranchomirage',
                    'name': 'Jaguar Rancho Mirage',
                    'base_url': 'https://www.jaguarranchomirage.com',
                    'scraper_class': JaguarRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'luxury',
                    'platform': 'dealeron',
                    'expected_models': ['F-PACE', 'E-PACE', 'I-PACE', 'XE', 'XF', 'XJ', 'F-TYPE']
                },
                'landrover': {
                    'id': 'landroverranchomirage',
                    'name': 'Land Rover Rancho Mirage',
                    'base_url': 'https://www.landroverofranchomirage.com',
                    'scraper_class': LandRoverRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'luxury',
                    'platform': 'dealeron',
                    'expected_models': ['Range Rover', 'Range Rover Sport', 'Discovery', 'Defender']
                },
                'astonmartin': {
                    'id': 'astonmartinranchomirage',
                    'name': 'Aston Martin Rancho Mirage',
                    'base_url': 'https://www.astonmartinranchomirage.com',
                    'scraper_class': AstonMartinRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'luxury',
                    'platform': 'dealeron',
                    'expected_models': ['DB11', 'DBS', 'Vantage', 'DBX']
                },
                'bentley': {
                    'id': 'bentleyranchomirage',
                    'name': 'Bentley Rancho Mirage',
                    'base_url': 'https://www.bentleyofranchomirage.com',
                    'scraper_class': BentleyRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'luxury',
                    'platform': 'dealeron',
                    'expected_models': ['Continental GT', 'Continental GTC', 'Flying Spur', 'Bentayga']
                },
                'mclaren': {
                    'id': 'mclarenranchomirage',
                    'name': 'McLaren Rancho Mirage',
                    'base_url': 'https://www.mclarenranchomirage.com',
                    'scraper_class': McLarenRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'supercar',
                    'platform': 'dealeron',
                    'expected_models': ['570S', '720S', 'Artura', 'GT']
                },
                'rollsroyce': {
                    'id': 'rollsroyceranchomirage',
                    'name': 'Rolls-Royce Motor Cars Rancho Mirage',
                    'base_url': 'https://www.rolls-roycemotorcarsranchomirage.com',
                    'scraper_class': RollsRoyceRanchoMirageWorkingScraper,
                    'group': 'ranch_mirage',
                    'tier': 'ultra_luxury',
                    'platform': 'dealeron',
                    'expected_models': ['Ghost', 'Phantom', 'Wraith', 'Dawn', 'Cullinan']
                }
            },
            
            # BMW Group
            'bmw': {
                'bmw_west_st_louis': {
                    'id': 'bmwofweststlouis',
                    'name': 'BMW of West St Louis',
                    'base_url': 'https://www.bmwofweststlouis.com',
                    'scraper_class': BMWofWestStLouisWorkingScraper,
                    'group': 'bmw',
                    'tier': 'luxury',
                    'platform': 'algolia',
                    'expected_models': ['3 Series', '4 Series', '5 Series', 'X3', 'X5', 'X7', 'i4', 'iX']
                }
            },
            
            # Suntrup Group
            'suntrup': {
                'suntrup_ford_west': {
                    'id': 'suntrupfordwest',
                    'name': 'Suntrup Ford West',
                    'base_url': 'https://www.suntrupfordwest.com',
                    'scraper_class': SuntrupFordWestWorkingScraper,
                    'group': 'suntrup',
                    'tier': 'mainstream',
                    'platform': 'dealeron',
                    'expected_models': ['F-150', 'Explorer', 'Escape', 'Edge', 'Mustang', 'Bronco']
                }
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for multi-dealership test suite"""
        logger = logging.getLogger('MultiDealershipTestSuite')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        log_filename = f"multi_dealership_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_test_config(self, tier: str):
        """Create test configuration based on dealership tier"""
        
        class TestConfig:
            def __init__(self, tier: str):
                if tier == "ultra_luxury":
                    self.request_delay = 8.0
                    self.timeout = 120
                elif tier == "supercar":
                    self.request_delay = 6.0
                    self.timeout = 90
                elif tier == "luxury":
                    self.request_delay = 4.0
                    self.timeout = 60
                elif tier == "premium":
                    self.request_delay = 3.0
                    self.timeout = 45
                else:  # mainstream
                    self.request_delay = 2.0
                    self.timeout = 30
        
        return TestConfig(tier)
    
    def test_optimization_framework_compatibility(self) -> bool:
        """Test that all optimization frameworks are compatible and working"""
        
        self.logger.info("🔧 Testing Multi-Dealership Optimization Framework Compatibility...")
        
        try:
            # Test multi-dealership framework creation
            ranch_optimizer = create_ranch_mirage_optimizer("Test Jaguar", "luxury")
            bmw_optimizer = create_bmw_optimizer("Test BMW")
            suntrup_optimizer = create_suntrup_optimizer("Test Suntrup")
            
            # Test framework detection
            auto_optimizer = detect_and_create_optimizer("BMW of Test", "https://bmw.example.com")
            
            # Test all have required methods
            optimizers = [ranch_optimizer, bmw_optimizer, suntrup_optimizer, auto_optimizer]
            required_methods = ['apply_request_optimization', 'get_optimized_headers', 'log_optimization_stats']
            
            for optimizer in optimizers:
                for method in required_methods:
                    if not hasattr(optimizer, method):
                        self.logger.error(f"❌ Optimizer missing method: {method}")
                        return False
            
            # Test user agent generation
            for optimizer in optimizers:
                if hasattr(optimizer, 'user_agent_manager'):
                    agent = optimizer.user_agent_manager.get_rotating_agent()
                    if not agent or len(agent) < 50:  # Basic validation
                        self.logger.error(f"❌ Invalid user agent: {agent}")
                        return False
            
            self.logger.info("✅ Multi-Dealership Optimization Framework compatibility test PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Framework compatibility test FAILED: {str(e)}")
            return False
    
    def test_dealership_group_initialization(self, group_name: str, group_configs: Dict[str, Dict]) -> Dict[str, bool]:
        """Test initialization for all dealerships in a group"""
        
        self.logger.info(f"🔧 Testing {group_name.upper()} dealership group initialization...")
        
        results = {}
        
        for dealership_key, config in group_configs.items():
            self.logger.info(f"  Testing {config['name']} initialization...")
            
            try:
                scraper_config = self._create_test_config(config['tier'])
                scraper = config['scraper_class'](config, scraper_config)
                
                # Test optimization framework integration
                if hasattr(scraper, 'optimizer'):
                    self.logger.info(f"    ✅ Optimization framework integrated")
                    
                    # Test optimization framework type
                    if hasattr(scraper.optimizer, 'framework_type'):
                        framework_type = getattr(scraper.optimizer, 'framework_type', 'Unknown')
                        self.logger.info(f"    🔧 Framework type: {framework_type}")
                    
                    # Test headers
                    if hasattr(scraper, 'headers') and 'User-Agent' in scraper.headers:
                        self.logger.info(f"    ✅ Optimized headers configured")
                    else:
                        self.logger.warning(f"    ⚠️ Header configuration issue")
                    
                    results[dealership_key] = True
                else:
                    self.logger.error(f"    ❌ No optimization framework found")
                    results[dealership_key] = False
                    
            except Exception as e:
                self.logger.error(f"    ❌ Initialization failed: {str(e)}")
                results[dealership_key] = False
        
        return results
    
    def test_dealership_group_functionality(self, group_name: str, group_configs: Dict[str, Dict], quick_test: bool = True) -> Dict[str, Dict]:
        """Test functionality for all dealerships in a group"""
        
        self.logger.info(f"🧪 Testing {group_name.upper()} dealership group functionality...")
        
        results = {}
        
        for dealership_key, config in group_configs.items():
            self.logger.info(f"  Testing {config['name']} functionality...")
            
            test_result = {
                'dealership': config['name'],
                'group': group_name,
                'tier': config['tier'],
                'platform': config['platform'],
                'success': False,
                'vehicles_found': 0,
                'optimization_used': False,
                'framework_type': 'Unknown',
                'execution_time': 0,
                'errors': []
            }
            
            start_time = time.time()
            
            try:
                scraper_config = self._create_test_config(config['tier'])
                scraper = config['scraper_class'](config, scraper_config)
                
                if hasattr(scraper, 'optimizer'):
                    test_result['optimization_used'] = True
                    test_result['framework_type'] = getattr(scraper.optimizer, 'framework_type', 'Unknown')
                
                # Quick functionality test - try to initialize basic components
                if quick_test:
                    # Test API/Chrome initialization without full scrape
                    if hasattr(scraper, '_initialize_dealer_info'):
                        # DealerOn-based dealerships
                        try:
                            init_success = scraper._initialize_dealer_info()
                            if init_success:
                                test_result['success'] = True
                                test_result['vehicles_found'] = 1  # Indicate successful connection
                                self.logger.info(f"    ✅ DealerOn API initialization successful")
                            else:
                                test_result['errors'].append("DealerOn initialization failed")
                                self.logger.warning(f"    ⚠️ DealerOn initialization failed")
                        except Exception as e:
                            test_result['errors'].append(f"DealerOn test error: {str(e)}")
                    
                    elif hasattr(scraper, '_scrape_vehicle_type_api'):
                        # Algolia-based dealerships (BMW)
                        try:
                            test_vehicles = scraper._scrape_vehicle_type_api('used')
                            test_result['vehicles_found'] = len(test_vehicles)
                            test_result['success'] = len(test_vehicles) > 0
                            if test_result['success']:
                                self.logger.info(f"    ✅ Algolia API test successful: {len(test_vehicles)} vehicles")
                            else:
                                self.logger.warning(f"    ⚠️ Algolia API returned no vehicles")
                        except Exception as e:
                            test_result['errors'].append(f"Algolia test error: {str(e)}")
                    
                    else:
                        # Generic test - just ensure scraper can be created
                        test_result['success'] = True
                        test_result['vehicles_found'] = 0  # No specific test
                        self.logger.info(f"    ✅ Scraper initialization successful")
                
                else:
                    # Full functionality test
                    vehicles = scraper.scrape_inventory()
                    test_result['vehicles_found'] = len(vehicles)
                    test_result['success'] = len(vehicles) > 0
                
                # Validate expected models if vehicles found
                if test_result['vehicles_found'] > 0 and not quick_test:
                    # Only do this for full tests to avoid extra API calls
                    pass  # Could add model validation here
                
            except Exception as e:
                test_result['errors'].append(str(e))
                self.logger.error(f"    ❌ Functionality test failed: {str(e)}")
            
            test_result['execution_time'] = time.time() - start_time
            results[dealership_key] = test_result
        
        return results
    
    def run_comprehensive_test(self, 
                             quick_test: bool = True, 
                             specific_groups: List[str] = None,
                             specific_dealerships: List[str] = None) -> None:
        """Run comprehensive test suite for all or specific dealership groups"""
        
        self.logger.info("🚀 Starting Multi-Dealership Optimization Test Suite")
        self.logger.info(f"Test type: {'Quick' if quick_test else 'Full'}")
        
        # Test 1: Framework Compatibility
        framework_success = self.test_optimization_framework_compatibility()
        
        if not framework_success:
            self.logger.error("❌ Framework compatibility test failed - stopping tests")
            return
        
        # Test 2: Group-by-group testing
        if specific_groups:
            groups_to_test = {k: v for k, v in self.dealership_configs.items() if k in specific_groups}
        else:
            groups_to_test = self.dealership_configs
        
        total_groups = len(groups_to_test)
        total_dealerships = 0
        successful_groups = 0
        successful_dealerships = 0
        
        for group_name, group_configs in groups_to_test.items():
            if specific_dealerships:
                # Filter dealerships within group
                group_configs = {k: v for k, v in group_configs.items() if k in specific_dealerships}
            
            if not group_configs:
                continue
                
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"TESTING {group_name.upper()} DEALERSHIP GROUP")
            self.logger.info(f"{'='*80}")
            
            total_dealerships += len(group_configs)
            
            # Test initialization
            init_results = self.test_dealership_group_initialization(group_name, group_configs)
            init_success_count = sum(1 for success in init_results.values() if success)
            
            # Test functionality  
            func_results = self.test_dealership_group_functionality(group_name, group_configs, quick_test)
            func_success_count = sum(1 for result in func_results.values() if result.get('success', False))
            
            # Store results
            self.results[group_name] = {
                'init_results': init_results,
                'func_results': func_results,
                'init_success_rate': init_success_count / len(group_configs) * 100,
                'func_success_rate': func_success_count / len(group_configs) * 100
            }
            
            successful_dealerships += func_success_count
            
            if func_success_count == len(group_configs):
                successful_groups += 1
                self.logger.info(f"✅ {group_name.upper()} group test PASSED - {func_success_count}/{len(group_configs)} dealerships working")
            else:
                self.logger.error(f"❌ {group_name.upper()} group test PARTIAL - {func_success_count}/{len(group_configs)} dealerships working")
        
        # Generate comprehensive summary
        self._generate_comprehensive_summary(total_groups, successful_groups, total_dealerships, successful_dealerships)
    
    def _generate_comprehensive_summary(self, total_groups: int, successful_groups: int, 
                                      total_dealerships: int, successful_dealerships: int) -> None:
        """Generate comprehensive test summary across all dealership groups"""
        
        test_duration = datetime.now() - self.test_start_time
        group_success_rate = (successful_groups / total_groups) * 100 if total_groups > 0 else 0
        dealership_success_rate = (successful_dealerships / total_dealerships) * 100 if total_dealerships > 0 else 0
        
        self.logger.info(f"\n{'='*100}")
        self.logger.info("🏁 MULTI-DEALERSHIP OPTIMIZATION TEST SUMMARY")
        self.logger.info(f"{'='*100}")
        self.logger.info(f"Total dealership groups tested: {total_groups}")
        self.logger.info(f"Successful groups: {successful_groups}")
        self.logger.info(f"Group success rate: {group_success_rate:.1f}%")
        self.logger.info(f"")
        self.logger.info(f"Total dealerships tested: {total_dealerships}")
        self.logger.info(f"Successful dealerships: {successful_dealerships}")
        self.logger.info(f"Dealership success rate: {dealership_success_rate:.1f}%")
        self.logger.info(f"Total test duration: {test_duration}")
        
        # Detailed results by group
        self.logger.info(f"\n📊 DETAILED RESULTS BY GROUP:")
        
        for group_name, group_results in self.results.items():
            func_results = group_results['func_results']
            init_rate = group_results['init_success_rate']
            func_rate = group_results['func_success_rate']
            
            self.logger.info(f"\n🏢 {group_name.upper()} GROUP:")
            self.logger.info(f"  Initialization: {init_rate:.1f}% success")
            self.logger.info(f"  Functionality: {func_rate:.1f}% success")
            
            for dealership_key, result in func_results.items():
                status = "✅ PASS" if result.get('success') else "❌ FAIL"
                vehicles = result.get('vehicles_found', 0)
                time_taken = result.get('execution_time', 0)
                framework = result.get('framework_type', 'Unknown')
                optimization = "🔧 Optimized" if result.get('optimization_used') else "⚠️ Basic"
                
                self.logger.info(f"    {status} {result['dealership']}: {vehicles} vehicles in {time_taken:.1f}s")
                self.logger.info(f"      Framework: {framework} {optimization} | Tier: {result['tier']} | Platform: {result['platform']}")
                
                if result.get('errors'):
                    for error in result['errors']:
                        self.logger.info(f"      ⚠️ {error}")
        
        # Framework usage statistics
        total_optimized = sum(
            sum(1 for result in group_results['func_results'].values() if result.get('optimization_used'))
            for group_results in self.results.values()
        )
        
        framework_types = {}
        for group_results in self.results.values():
            for result in group_results['func_results'].values():
                framework_type = result.get('framework_type', 'Unknown')
                framework_types[framework_type] = framework_types.get(framework_type, 0) + 1
        
        self.logger.info(f"\n🔧 OPTIMIZATION FRAMEWORK USAGE:")
        self.logger.info(f"  Total scrapers using optimization: {total_optimized}/{total_dealerships}")
        self.logger.info(f"  Framework distribution:")
        for framework, count in framework_types.items():
            self.logger.info(f"    {framework}: {count}")
        
        # Overall assessment
        if dealership_success_rate >= 90:
            self.logger.info(f"\n🎉 EXCELLENT! Multi-dealership optimization system is performing exceptionally!")
        elif dealership_success_rate >= 75:
            self.logger.info(f"\n👍 GOOD! Most dealership groups are working well with optimization.")
        elif dealership_success_rate >= 50:
            self.logger.info(f"\n⚠️ MIXED RESULTS! Some dealership groups need attention.")
        else:
            self.logger.info(f"\n🚨 NEEDS ATTENTION! Multiple dealership groups require debugging.")

def main():
    """Main multi-dealership test execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Dealership Optimization Test Suite')
    parser.add_argument('--full', action='store_true', help='Run full test (slower)')
    parser.add_argument('--groups', nargs='+', 
                       choices=['ranch_mirage', 'bmw', 'suntrup'],
                       help='Test specific dealership groups only')
    parser.add_argument('--dealerships', nargs='+',
                       help='Test specific dealerships only (by key)')
    
    args = parser.parse_args()
    
    test_suite = MultiDealershipTestSuite()
    
    quick_test = not args.full
    specific_groups = args.groups
    specific_dealerships = args.dealerships
    
    test_suite.run_comprehensive_test(
        quick_test=quick_test, 
        specific_groups=specific_groups,
        specific_dealerships=specific_dealerships
    )

if __name__ == "__main__":
    main()