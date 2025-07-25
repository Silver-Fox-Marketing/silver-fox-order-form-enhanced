#!/usr/bin/env python3
"""
PipeDrive CRM Integration Test Suite
Comprehensive testing for PipeDrive integration with Silver Fox scraper system
Tests vehicle sync, alerts integration, competitive insights, and stress testing
"""

import os
import sys
import logging
import time
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from unittest.mock import Mock, patch
import concurrent.futures
import threading

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(parent_dir, 'utils')
sys.path.append(parent_dir)
sys.path.append(utils_dir)

# Import modules to test
try:
    from pipedrive_crm_integration import (
        PipeDriveCRMIntegration,
        PipeDriveConfiguration,
        VehicleDeal,
        CompetitorInsight,
        create_pipedrive_integration
    )
    from realtime_inventory_alerts import (
        InventoryAlert,
        AlertType,
        AlertPriority,
        NotificationChannel
    )
    from competitive_pricing_analysis import CompetitivePricingAnalysis
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

@dataclass
class TestConfiguration:
    """Test configuration for PipeDrive integration"""
    mock_api: bool = True  # Use mock API instead of real PipeDrive
    stress_test_duration: int = 300  # 5 minutes
    concurrent_threads: int = 10
    vehicles_per_batch: int = 100
    alerts_per_batch: int = 50
    insights_per_batch: int = 25
    dealership_count: int = 6  # Ranch Mirage dealerships

class PipeDriveIntegrationTestSuite:
    """Comprehensive test suite for PipeDrive CRM integration"""
    
    def __init__(self, test_config: TestConfiguration):
        self.test_config = test_config
        self.logger = self._setup_logging()
        
        # Test results tracking
        self.test_results = {}
        self.stress_test_results = {}
        self.performance_metrics = {}
        
        # Mock data generators
        self.mock_vehicles = []
        self.mock_alerts = []
        self.mock_insights = []
        
        # Thread safety
        self.results_lock = threading.Lock()
        self.error_count = 0
        self.success_count = 0
        
        # Initialize test environment
        self._initialize_test_environment()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for tests"""
        logger = logging.getLogger('PipeDriveIntegrationTest')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_filename = f"pipedrive_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _initialize_test_environment(self):
        """Initialize test environment with mock data"""
        
        self.logger.info("🔧 Initializing PipeDrive integration test environment...")
        
        # Generate mock vehicle data
        self._generate_mock_vehicles()
        
        # Generate mock alerts
        self._generate_mock_alerts()
        
        # Generate mock competitive insights
        self._generate_mock_insights()
        
        self.logger.info(f"✅ Test environment initialized:")
        self.logger.info(f"   Mock vehicles: {len(self.mock_vehicles)}")
        self.logger.info(f"   Mock alerts: {len(self.mock_alerts)}")
        self.logger.info(f"   Mock insights: {len(self.mock_insights)}")
    
    def _generate_mock_vehicles(self):
        """Generate realistic mock vehicle data"""
        
        dealerships = [
            "Jaguar Rancho Mirage",
            "Land Rover Rancho Mirage", 
            "Aston Martin Rancho Mirage",
            "Bentley Rancho Mirage",
            "McLaren Rancho Mirage",
            "Rolls-Royce Motor Cars Rancho Mirage"
        ]
        
        makes_models = {
            "Jaguar": ["F-PACE", "E-PACE", "I-PACE", "XE", "XF", "XJ", "F-TYPE"],
            "Land Rover": ["Range Rover", "Range Rover Sport", "Discovery", "Defender"],
            "Aston Martin": ["DB11", "DBS", "Vantage", "DBX"],
            "Bentley": ["Continental GT", "Continental GTC", "Flying Spur", "Bentayga"],
            "McLaren": ["570S", "720S", "Artura", "GT"],
            "Rolls-Royce": ["Ghost", "Phantom", "Wraith", "Dawn", "Cullinan"]
        }
        
        colors = ["Black", "White", "Silver", "Gray", "Red", "Blue", "Green", "Brown"]
        conditions = ["New", "Used", "Certified"]
        
        for i in range(self.test_config.vehicles_per_batch * self.test_config.dealership_count):
            dealership = random.choice(dealerships)
            make = dealership.split()[0]
            model = random.choice(makes_models.get(make, ["Unknown"]))
            
            vehicle = {
                'vin': self._generate_mock_vin(),
                'stock_number': f"STK{random.randint(10000, 99999)}",
                'year': random.randint(2018, 2024),
                'make': make,
                'model': model,
                'trim': f"{model} Premium" if random.choice([True, False]) else model,
                'price': random.randint(50000, 500000),
                'msrp': random.randint(55000, 550000),
                'mileage': random.randint(0, 50000) if random.choice([True, False]) else 0,
                'exterior_color': random.choice(colors),
                'interior_color': random.choice(colors),
                'transmission': random.choice(["Automatic", "Manual"]),
                'engine': f"{random.choice(['3.0L', '4.0L', '5.0L', '6.0L'])} V{random.choice([6, 8, 12])}",
                'fuel_type': random.choice(["Gasoline", "Hybrid", "Electric"]),
                'condition': random.choice(conditions),
                'dealer_name': dealership,
                'dealer_address': "123 Luxury Way",
                'dealer_city': "Rancho Mirage",
                'dealer_state': "CA",
                'dealer_zip': "92270",
                'vehicle_url': f"https://www.{dealership.lower().replace(' ', '')}.com/vehicle/{self._generate_mock_vin()}",
                'scraped_at': datetime.now().isoformat()
            }
            
            self.mock_vehicles.append(vehicle)
    
    def _generate_mock_alerts(self):
        """Generate mock inventory alerts"""
        
        alert_types = [AlertType.NEW_VEHICLE, AlertType.PRICE_DROP, AlertType.INVENTORY_LOW, 
                      AlertType.SOLD_VEHICLE, AlertType.VERIFICATION_FAILURE]
        priorities = [AlertPriority.CRITICAL, AlertPriority.HIGH, AlertPriority.MEDIUM, AlertPriority.LOW]
        dealerships = ["Jaguar Rancho Mirage", "Land Rover Rancho Mirage", "McLaren Rancho Mirage"]
        
        for i in range(self.test_config.alerts_per_batch):
            alert_type = random.choice(alert_types)
            priority = random.choice(priorities)
            dealership = random.choice(dealerships)
            
            alert = InventoryAlert(
                alert_id=f"alert_{int(time.time() * 1000000)}_{i}",
                alert_type=alert_type,
                priority=priority,
                dealership_name=dealership,
                dealership_id=dealership.lower().replace(' ', '_'),
                title=f"{alert_type.value.replace('_', ' ').title()} Alert",
                message=f"Test alert message for {dealership}",
                details={
                    'test_data': True,
                    'vehicle_count': random.randint(1, 50),
                    'price_change': random.randint(-10000, 10000) if alert_type == AlertType.PRICE_DROP else None
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK]
            )
            
            self.mock_alerts.append(alert)
    
    def _generate_mock_insights(self):
        """Generate mock competitive insights"""
        
        dealerships = ["Jaguar Rancho Mirage", "BMW West St Louis", "Suntrup Ford West"]
        competitors = ["Local Competitor A", "Local Competitor B", "Regional Dealer"]
        positions = ["SIGNIFICANTLY_BELOW", "BELOW", "COMPETITIVE", "ABOVE", "SIGNIFICANTLY_ABOVE"]
        
        for i in range(self.test_config.insights_per_batch):
            our_price = random.randint(30000, 200000)
            competitor_price = random.randint(25000, 220000)
            
            insight = CompetitorInsight(
                vin=self._generate_mock_vin(),
                competitor_dealership=random.choice(competitors),
                our_price=our_price,
                competitor_price=competitor_price,
                price_advantage=our_price - competitor_price,
                market_position=random.choice(positions),
                insight_text=f"Vehicle priced {'competitively' if abs(our_price - competitor_price) < 5000 else 'strategically'}",
                priority="high" if abs(our_price - competitor_price) > 10000 else "medium"
            )
            
            self.mock_insights.append(insight)
    
    def _generate_mock_vin(self) -> str:
        """Generate realistic mock VIN"""
        import string
        # VIN format: 1-3 digits + 14 alphanumeric (excluding I, O, Q)
        vin_chars = string.digits + "ABCDEFGHJKLMNPRSTUVWXYZ"
        return ''.join(random.choices(vin_chars, k=17))
    
    def _create_mock_pipedrive_integration(self) -> PipeDriveCRMIntegration:
        """Create PipeDrive integration with mocked API calls"""
        
        config = PipeDriveConfiguration(
            api_token="mock_token_12345",
            company_domain="silverfox-test",
            pipeline_id=1,
            stage_mapping={'new': 1, 'qualified': 2, 'proposal': 3},
            custom_field_mapping={
                'vin': 1001,
                'stock_number': 1002,
                'mileage': 1003,
                'exterior_color': 1004,
                'dealership_name': 1005
            }
        )
        
        integration = PipeDriveCRMIntegration(config)
        
        if self.test_config.mock_api:
            # Mock all API calls
            integration._make_api_request = self._mock_api_request
            integration._verify_api_connection = lambda: True
            integration._cache_pipeline_info = lambda: None
            integration._cache_custom_fields = lambda: None
        
        return integration
    
    def _mock_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock API request for testing"""
        
        # Simulate API latency
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simulate occasional failures for stress testing
        if random.random() < 0.05:  # 5% failure rate
            return {'success': False, 'error': 'Mock API failure'}
        
        # Return mock successful responses
        if 'deals' in endpoint:
            if method == 'POST':
                return {
                    'success': True,
                    'data': {
                        'id': random.randint(1000, 9999),
                        'title': data.get('title', 'Mock Deal'),
                        'value': data.get('value', 0)
                    }
                }
            elif method == 'GET':
                return {
                    'success': True,
                    'data': {
                        'items': [
                            {
                                'id': random.randint(1000, 9999),
                                'title': 'Mock Deal',
                                'custom_fields': [{'key': 'vin', 'value': self._generate_mock_vin()}]
                            }
                        ]
                    }
                }
            elif method == 'PUT':
                return {'success': True, 'data': {'id': params.get('id', 1000)}}
        
        elif 'products' in endpoint:
            if method == 'POST':
                return {
                    'success': True,
                    'data': {
                        'id': random.randint(2000, 9999),
                        'name': data.get('name', 'Mock Product')
                    }
                }
        
        elif 'activities' in endpoint or 'notes' in endpoint:
            return {
                'success': True,
                'data': {
                    'id': random.randint(3000, 9999)
                }
            }
        
        return {'success': True, 'data': {}}
    
    def test_basic_integration_functionality(self) -> bool:
        """Test basic PipeDrive integration functionality"""
        
        self.logger.info("🧪 Testing basic PipeDrive integration functionality...")
        
        try:
            # Create integration instance
            integration = self._create_mock_pipedrive_integration()
            
            # Test vehicle sync with small batch
            test_vehicles = self.mock_vehicles[:5]
            sync_report = integration.sync_vehicle_inventory(test_vehicles, "Test Dealership")
            
            # Verify sync report structure
            expected_fields = ['dealership', 'total_vehicles', 'deals_created', 'deals_updated', 'sync_duration']
            for field in expected_fields:
                if field not in sync_report:
                    self.logger.error(f"❌ Missing field in sync report: {field}")
                    return False
            
            # Test alert sync
            test_alerts = self.mock_alerts[:3]
            alert_report = integration.sync_inventory_alerts(test_alerts)
            
            if 'total_alerts' not in alert_report:
                self.logger.error("❌ Alert sync report missing total_alerts field")
                return False
            
            # Test competitive insights sync
            test_insights = self.mock_insights[:2]
            insight_report = integration.sync_competitive_insights(test_insights)
            
            if 'total_insights' not in insight_report:
                self.logger.error("❌ Insight sync report missing total_insights field")
                return False
            
            self.logger.info("✅ Basic integration functionality test PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Basic integration test FAILED: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and resilience"""
        
        self.logger.info("🛡️ Testing error handling and resilience...")
        
        try:
            integration = self._create_mock_pipedrive_integration()
            
            # Test with invalid vehicle data
            invalid_vehicles = [
                {'invalid': 'data'},  # Missing required fields
                {},  # Empty vehicle
                {'vin': '', 'make': None}  # Invalid values
            ]
            
            sync_report = integration.sync_vehicle_inventory(invalid_vehicles, "Test Dealership")
            
            # Should handle errors gracefully
            if 'errors' not in sync_report:
                self.logger.error("❌ Sync report should include errors field")
                return False
            
            # Test with malformed alerts
            invalid_alerts = [Mock(alert_id="invalid", title=None, message="test")]
            
            try:
                integration.sync_inventory_alerts(invalid_alerts)
                # Should not crash
            except Exception as e:
                self.logger.error(f"❌ Alert sync should handle errors gracefully: {str(e)}")
                return False
            
            self.logger.info("✅ Error handling test PASSED")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error handling test FAILED: {str(e)}")
            return False
    
    def test_concurrent_operations(self) -> bool:
        """Test concurrent operations and thread safety"""
        
        self.logger.info("🔄 Testing concurrent operations and thread safety...")
        
        try:
            integration = self._create_mock_pipedrive_integration()
            
            # Reset counters
            self.success_count = 0
            self.error_count = 0
            
            def sync_worker(worker_id: int, vehicles: List[Dict]):
                """Worker function for concurrent testing"""
                try:
                    dealership_name = f"Test Dealership {worker_id}"
                    sync_report = integration.sync_vehicle_inventory(vehicles, dealership_name)
                    
                    with self.results_lock:
                        if sync_report.get('deals_created', 0) > 0 or sync_report.get('deals_updated', 0) > 0:
                            self.success_count += 1
                        if sync_report.get('errors'):
                            self.error_count += len(sync_report['errors'])
                
                except Exception as e:
                    with self.results_lock:
                        self.error_count += 1
                        self.logger.error(f"Worker {worker_id} error: {str(e)}")
            
            # Create worker threads
            vehicles_per_worker = len(self.mock_vehicles) // self.test_config.concurrent_threads
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.test_config.concurrent_threads) as executor:
                futures = []
                
                for i in range(self.test_config.concurrent_threads):
                    start_idx = i * vehicles_per_worker
                    end_idx = start_idx + vehicles_per_worker
                    worker_vehicles = self.mock_vehicles[start_idx:end_idx]
                    
                    future = executor.submit(sync_worker, i, worker_vehicles)
                    futures.append(future)
                
                # Wait for all workers to complete
                concurrent.futures.wait(futures)
            
            # Evaluate results
            total_operations = self.success_count + self.error_count
            success_rate = (self.success_count / total_operations * 100) if total_operations > 0 else 0
            
            self.logger.info(f"Concurrent operations completed:")
            self.logger.info(f"  Successful operations: {self.success_count}")
            self.logger.info(f"  Failed operations: {self.error_count}")
            self.logger.info(f"  Success rate: {success_rate:.1f}%")
            
            # Consider test passed if success rate > 90%
            if success_rate > 90:
                self.logger.info("✅ Concurrent operations test PASSED")
                return True
            else:
                self.logger.error(f"❌ Concurrent operations test FAILED - Low success rate: {success_rate:.1f}%")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Concurrent operations test FAILED: {str(e)}")
            return False
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run comprehensive stress test of PipeDrive integration"""
        
        self.logger.info("🚀 Starting PipeDrive integration stress test...")
        self.logger.info(f"   Duration: {self.test_config.stress_test_duration} seconds")
        self.logger.info(f"   Concurrent threads: {self.test_config.concurrent_threads}")
        self.logger.info(f"   Vehicles per batch: {self.test_config.vehicles_per_batch}")
        
        stress_results = {
            'start_time': datetime.now(),
            'duration': self.test_config.stress_test_duration,
            'concurrent_threads': self.test_config.concurrent_threads,
            'operations_completed': 0,
            'operations_failed': 0,
            'api_calls_made': 0,
            'avg_response_time': 0.0,
            'peak_response_time': 0.0,
            'memory_usage': [],
            'error_details': [],
            'throughput_metrics': []
        }
        
        integration = self._create_mock_pipedrive_integration()
        
        # Performance tracking
        operation_times = []
        operation_count = 0
        error_count = 0
        
        def stress_worker(worker_id: int):
            """Stress test worker function"""
            nonlocal operation_count, error_count
            
            start_time = time.time()
            worker_operations = 0
            worker_errors = 0
            
            while time.time() - start_time < self.test_config.stress_test_duration:
                try:
                    # Vehicle inventory sync
                    batch_start = time.time()
                    vehicles_batch = random.sample(self.mock_vehicles, min(50, len(self.mock_vehicles)))
                    sync_report = integration.sync_vehicle_inventory(vehicles_batch, f"Stress Test Dealership {worker_id}")
                    operation_time = time.time() - batch_start
                    operation_times.append(operation_time)
                    
                    worker_operations += 1
                    
                    # Alert sync (periodic)
                    if worker_operations % 5 == 0:
                        alerts_batch = random.sample(self.mock_alerts, min(10, len(self.mock_alerts)))
                        integration.sync_inventory_alerts(alerts_batch)
                    
                    # Insights sync (periodic)
                    if worker_operations % 10 == 0:
                        insights_batch = random.sample(self.mock_insights, min(5, len(self.mock_insights)))
                        integration.sync_competitive_insights(insights_batch)
                    
                    # Small delay between operations
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    worker_errors += 1
                    stress_results['error_details'].append({
                        'worker_id': worker_id,
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    })
            
            with self.results_lock:
                operation_count += worker_operations
                error_count += worker_errors
        
        # Run stress test with multiple workers
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.test_config.concurrent_threads) as executor:
            futures = [
                executor.submit(stress_worker, i) 
                for i in range(self.test_config.concurrent_threads)
            ]
            
            # Monitor progress
            while not all(future.done() for future in futures):
                time.sleep(10)  # Progress update every 10 seconds
                elapsed = time.time() - start_time
                self.logger.info(f"⏱️ Stress test progress: {elapsed:.0f}/{self.test_config.stress_test_duration}s")
            
            # Wait for completion
            concurrent.futures.wait(futures)
        
        # Calculate final metrics
        total_duration = time.time() - start_time
        
        stress_results.update({
            'end_time': datetime.now(),
            'actual_duration': total_duration,
            'operations_completed': operation_count,
            'operations_failed': error_count,
            'success_rate': (operation_count / (operation_count + error_count) * 100) if (operation_count + error_count) > 0 else 0,
            'operations_per_second': operation_count / total_duration if total_duration > 0 else 0,
            'avg_response_time': sum(operation_times) / len(operation_times) if operation_times else 0,
            'peak_response_time': max(operation_times) if operation_times else 0,
            'min_response_time': min(operation_times) if operation_times else 0
        })
        
        self.stress_test_results = stress_results
        return stress_results
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite for PipeDrive integration"""
        
        self.logger.info("🎯 Starting comprehensive PipeDrive integration test suite...")
        
        test_suite_results = {
            'start_time': datetime.now(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': {},
            'stress_test_results': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Test 1: Basic functionality
        self.logger.info("\n" + "="*80)
        self.logger.info("TEST 1: Basic Integration Functionality")
        self.logger.info("="*80)
        
        basic_test_passed = self.test_basic_integration_functionality()
        test_suite_results['tests_run'] += 1
        test_suite_results['test_details']['basic_functionality'] = {
            'passed': basic_test_passed,
            'description': 'Tests core vehicle sync, alert sync, and insight sync functionality'
        }
        
        if basic_test_passed:
            test_suite_results['tests_passed'] += 1
        else:
            test_suite_results['tests_failed'] += 1
        
        # Test 2: Error handling
        self.logger.info("\n" + "="*80)
        self.logger.info("TEST 2: Error Handling and Resilience")
        self.logger.info("="*80)
        
        error_test_passed = self.test_error_handling()
        test_suite_results['tests_run'] += 1
        test_suite_results['test_details']['error_handling'] = {
            'passed': error_test_passed,
            'description': 'Tests graceful handling of invalid data and API failures'
        }
        
        if error_test_passed:
            test_suite_results['tests_passed'] += 1
        else:
            test_suite_results['tests_failed'] += 1
        
        # Test 3: Concurrent operations
        self.logger.info("\n" + "="*80)
        self.logger.info("TEST 3: Concurrent Operations and Thread Safety")
        self.logger.info("="*80)
        
        concurrent_test_passed = self.test_concurrent_operations()
        test_suite_results['tests_run'] += 1
        test_suite_results['test_details']['concurrent_operations'] = {
            'passed': concurrent_test_passed,
            'description': 'Tests thread safety and concurrent API operations'
        }
        
        if concurrent_test_passed:
            test_suite_results['tests_passed'] += 1
        else:
            test_suite_results['tests_failed'] += 1
        
        # Test 4: Stress test
        self.logger.info("\n" + "="*80)
        self.logger.info("TEST 4: Comprehensive Stress Test")
        self.logger.info("="*80)
        
        stress_results = self.run_stress_test()
        test_suite_results['stress_test_results'] = stress_results
        
        # Evaluate stress test
        stress_success_rate = stress_results.get('success_rate', 0)
        operations_per_second = stress_results.get('operations_per_second', 0)
        
        stress_test_passed = (
            stress_success_rate >= 85 and  # 85% success rate
            operations_per_second >= 5     # At least 5 operations per second
        )
        
        test_suite_results['tests_run'] += 1
        test_suite_results['test_details']['stress_test'] = {
            'passed': stress_test_passed,
            'description': f'Stress test with {stress_success_rate:.1f}% success rate, {operations_per_second:.1f} ops/sec',
            'success_rate': stress_success_rate,
            'operations_per_second': operations_per_second
        }
        
        if stress_test_passed:
            test_suite_results['tests_passed'] += 1
        else:
            test_suite_results['tests_failed'] += 1
        
        # Calculate overall status
        test_suite_results['end_time'] = datetime.now()
        test_suite_results['total_duration'] = (test_suite_results['end_time'] - test_suite_results['start_time']).total_seconds()
        
        if test_suite_results['tests_failed'] == 0:
            test_suite_results['overall_status'] = 'PASSED'
        elif test_suite_results['tests_passed'] >= test_suite_results['tests_failed']:
            test_suite_results['overall_status'] = 'MOSTLY_PASSED'
        else:
            test_suite_results['overall_status'] = 'FAILED'
        
        # Log comprehensive summary
        self._log_test_suite_summary(test_suite_results)
        
        return test_suite_results
    
    def _log_test_suite_summary(self, results: Dict[str, Any]):
        """Log comprehensive test suite summary"""
        
        self.logger.info("\n" + "="*100)
        self.logger.info("🏁 PIPEDRIVE INTEGRATION TEST SUITE SUMMARY")
        self.logger.info("="*100)
        
        # Overall results
        self.logger.info(f"Overall Status: {results['overall_status']}")
        self.logger.info(f"Tests Run: {results['tests_run']}")
        self.logger.info(f"Tests Passed: {results['tests_passed']}")
        self.logger.info(f"Tests Failed: {results['tests_failed']}")
        self.logger.info(f"Success Rate: {(results['tests_passed'] / results['tests_run'] * 100):.1f}%")
        self.logger.info(f"Total Duration: {results['total_duration']:.1f} seconds")
        
        # Individual test results
        self.logger.info(f"\n📊 INDIVIDUAL TEST RESULTS:")
        for test_name, test_data in results['test_details'].items():
            status = "✅ PASS" if test_data['passed'] else "❌ FAIL"
            self.logger.info(f"  {status} {test_name.replace('_', ' ').title()}")
            self.logger.info(f"    {test_data['description']}")
        
        # Stress test detailed results
        if 'stress_test_results' in results:
            stress_results = results['stress_test_results']
            self.logger.info(f"\n🚀 STRESS TEST DETAILED RESULTS:")
            self.logger.info(f"  Operations Completed: {stress_results.get('operations_completed', 0)}")
            self.logger.info(f"  Operations Failed: {stress_results.get('operations_failed', 0)}")
            self.logger.info(f"  Success Rate: {stress_results.get('success_rate', 0):.1f}%")
            self.logger.info(f"  Operations/Second: {stress_results.get('operations_per_second', 0):.1f}")
            self.logger.info(f"  Avg Response Time: {stress_results.get('avg_response_time', 0):.3f}s")
            self.logger.info(f"  Peak Response Time: {stress_results.get('peak_response_time', 0):.3f}s")
            self.logger.info(f"  Concurrent Threads: {stress_results.get('concurrent_threads', 0)}")
            
            error_count = len(stress_results.get('error_details', []))
            if error_count > 0:
                self.logger.info(f"  Errors Encountered: {error_count}")
        
        # Performance assessment
        self.logger.info(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if results['overall_status'] == 'PASSED':
            self.logger.info("  🎉 EXCELLENT! PipeDrive integration is performing exceptionally well!")
            self.logger.info("  🔥 Ready for production deployment with full confidence.")
        elif results['overall_status'] == 'MOSTLY_PASSED':
            self.logger.info("  👍 GOOD! PipeDrive integration is working well with minor issues.")
            self.logger.info("  ⚠️ Review failed tests and consider optimizations before deployment.")
        else:
            self.logger.info("  🚨 NEEDS ATTENTION! Multiple test failures detected.")
            self.logger.info("  🛠️ Significant debugging and optimization required before deployment.")
        
        self.logger.info("="*100)

def main():
    """Main test execution function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='PipeDrive CRM Integration Test Suite')
    parser.add_argument('--mock-api', action='store_true', default=True,
                       help='Use mock API (default: True)')
    parser.add_argument('--stress-duration', type=int, default=300,
                       help='Stress test duration in seconds (default: 300)')
    parser.add_argument('--concurrent-threads', type=int, default=10,
                       help='Number of concurrent threads (default: 10)')
    parser.add_argument('--vehicles-per-batch', type=int, default=100,
                       help='Vehicles per test batch (default: 100)')
    
    args = parser.parse_args()
    
    # Create test configuration
    test_config = TestConfiguration(
        mock_api=args.mock_api,
        stress_test_duration=args.stress_duration,
        concurrent_threads=args.concurrent_threads,
        vehicles_per_batch=args.vehicles_per_batch
    )
    
    # Run comprehensive test suite
    test_suite = PipeDriveIntegrationTestSuite(test_config)
    results = test_suite.run_comprehensive_test_suite()
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASSED':
        print(f"\n🎉 All tests PASSED! PipeDrive integration is ready for production.")
        sys.exit(0)
    elif results['overall_status'] == 'MOSTLY_PASSED':
        print(f"\n⚠️ Most tests passed with some issues. Review and optimize before deployment.")
        sys.exit(1)
    else:
        print(f"\n❌ Multiple test failures. Significant work needed before deployment.")
        sys.exit(2)

if __name__ == "__main__":
    main()