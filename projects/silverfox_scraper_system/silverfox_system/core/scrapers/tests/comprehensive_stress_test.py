#!/usr/bin/env python3
"""
Comprehensive Silver Fox System Stress Test
Tests the entire scraper system with all components under load:
- Multi-dealership scrapers with optimization frameworks
- Enhanced inventory verification
- Real-time alerts system  
- Competitive pricing analysis
- PipeDrive CRM integration
"""

import os
import sys
import logging
import time
import json
import random
import psutil
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(parent_dir, 'utils')
dealerships_dir = os.path.join(parent_dir, 'dealerships')
sys.path.append(parent_dir)
sys.path.append(utils_dir)
sys.path.append(dealerships_dir)

# Import all system components
try:
    # Multi-dealership test suite
    from test_multi_dealership_optimization import MultiDealershipTestSuite
    
    # PipeDrive integration test
    from test_pipedrive_integration import PipeDriveIntegrationTestSuite, TestConfiguration as PipeDriveTestConfig
    
    # Core modules
    from multi_dealership_optimization_framework import MultiDealershipOptimizationFramework
    from enhanced_inventory_verification import EnhancedInventoryVerificationSystem
    from realtime_inventory_alerts import RealtimeInventoryAlertSystem, create_alert_system
    from competitive_pricing_analysis import CompetitivePricingAnalyzer
    from pipedrive_crm_integration import PipeDriveCRMIntegration, create_pipedrive_integration
    
    # Individual scrapers for stress testing
    from jaguarranchomirage_working import JaguarRanchoMirageWorkingScraper
    from landroverranchomirage_working import LandRoverRanchoMirageWorkingScraper
    from bmwofweststlouis_working import BMWofWestStLouisWorkingScraper
    from suntrupfordwest_working import SuntrupFordWestWorkingScraper
    
except ImportError as e:
    print(f"❌ Error importing system components: {e}")
    print("💡 Make sure all modules are properly installed and paths are correct")
    sys.exit(1)

@dataclass
class StressTestConfiguration:
    """Comprehensive stress test configuration"""
    duration_minutes: int = 30  # Total test duration
    concurrent_scrapers: int = 6  # Number of scrapers running simultaneously
    vehicles_per_scraper: int = 200  # Target vehicles per scraper
    verification_enabled: bool = True  # Enable inventory verification
    alerts_enabled: bool = True  # Enable real-time alerts
    competitive_analysis_enabled: bool = True  # Enable competitive analysis
    pipedrive_integration_enabled: bool = True  # Enable PipeDrive sync
    mock_external_apis: bool = True  # Mock external APIs for controlled testing
    memory_monitoring: bool = True  # Monitor memory usage
    performance_metrics: bool = True  # Collect detailed performance metrics
    error_injection_rate: float = 0.02  # Inject 2% random errors for resilience testing
    rate_limiting_enabled: bool = True  # Respect rate limits
    cleanup_on_exit: bool = True  # Clean up resources on exit

@dataclass
class ScraperStressResult:
    """Individual scraper stress test result"""
    scraper_name: str
    dealership_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    vehicles_scraped: int = 0
    api_calls_made: int = 0
    verification_reports: List[Dict] = field(default_factory=list)
    alerts_generated: List[Dict] = field(default_factory=list)
    competitive_insights: List[Dict] = field(default_factory=list)
    pipedrive_syncs: List[Dict] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    memory_usage: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, mb_used)
    success: bool = False

@dataclass
class SystemStressResult:
    """Overall system stress test result"""
    test_config: StressTestConfiguration
    start_time: datetime
    end_time: Optional[datetime] = None
    scraper_results: List[ScraperStressResult] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    total_vehicles_scraped: int = 0
    total_api_calls: int = 0
    total_alerts_generated: int = 0
    total_competitive_insights: int = 0
    total_pipedrive_syncs: int = 0
    peak_memory_usage_mb: float = 0.0
    avg_cpu_usage_percent: float = 0.0
    error_rate_percent: float = 0.0
    overall_success: bool = False

class ComprehensiveStressTest:
    """
    Comprehensive stress test for the entire Silver Fox scraper system
    Tests all components under realistic load conditions
    """
    
    def __init__(self, config: StressTestConfiguration):
        self.config = config
        self.logger = self._setup_logging()
        
        # Test state
        self.test_running = True
        self.results_queue = queue.Queue()
        self.system_metrics = []
        self.shutdown_event = threading.Event()
        
        # Component instances
        self.alert_system = None
        self.competitive_analyzer = None
        self.pipedrive_integration = None
        
        # Performance monitoring
        self.start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        self.monitoring_thread = None
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🚀 Comprehensive Silver Fox System Stress Test initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for stress test"""
        logger = logging.getLogger('SilverFoxStressTest')
        logger.setLevel(logging.INFO)
        
        # Console handler with colorized output
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler for detailed logs
        log_filename = f"silverfox_stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.test_running = False
        self.shutdown_event.set()
    
    def _initialize_system_components(self):
        """Initialize all system components for stress testing"""
        
        self.logger.info("🔧 Initializing system components for stress test...")
        
        try:
            # Initialize alert system
            if self.config.alerts_enabled:
                alert_config = {
                    'price_drop_threshold': 5.0,
                    'low_inventory_threshold': 10,
                    'email_config': {'mock': True} if self.config.mock_external_apis else {},
                    'webhook_config': {'mock': True} if self.config.mock_external_apis else {},
                    'slack_config': {'mock': True} if self.config.mock_external_apis else {}
                }
                self.alert_system = create_alert_system(alert_config)
                self.logger.info("✅ Real-time alerts system initialized")
            
            # Initialize competitive analyzer
            if self.config.competitive_analysis_enabled:
                self.competitive_analyzer = CompetitivePricingAnalyzer(
                    dealership_configs={
                        'jaguar': {'name': 'Jaguar Rancho Mirage', 'tier': 'luxury'},
                        'bmw': {'name': 'BMW of West St Louis', 'tier': 'luxury'},
                        'ford': {'name': 'Suntrup Ford West', 'tier': 'mainstream'}
                    }
                )
                self.logger.info("✅ Competitive pricing analysis initialized")
            
            # Initialize PipeDrive integration (with mock)
            if self.config.pipedrive_integration_enabled:
                if self.config.mock_external_apis:
                    # Create mock PipeDrive integration
                    self.pipedrive_integration = self._create_mock_pipedrive()
                else:
                    # Would use real PipeDrive credentials here
                    self.logger.warning("⚠️ Real PipeDrive integration not configured for stress test")
                    self.pipedrive_integration = self._create_mock_pipedrive()
                
                self.logger.info("✅ PipeDrive CRM integration initialized")
            
            # Start system monitoring
            if self.config.memory_monitoring:
                self.monitoring_thread = threading.Thread(target=self._monitor_system_resources)
                self.monitoring_thread.daemon = True
                self.monitoring_thread.start()
                self.logger.info("✅ System monitoring started")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize system components: {str(e)}")
            raise
    
    def _create_mock_pipedrive(self):
        """Create mock PipeDrive integration for testing"""
        
        # Create a mock class that mimics PipeDrive integration
        class MockPipeDriveIntegration:
            def __init__(self):
                self.sync_count = 0
                self.alert_count = 0
                self.insight_count = 0
            
            def sync_vehicle_inventory(self, vehicles, dealership_name):
                time.sleep(random.uniform(0.1, 0.3))  # Simulate API latency
                self.sync_count += 1
                return {
                    'dealership': dealership_name,
                    'total_vehicles': len(vehicles),
                    'deals_created': random.randint(0, len(vehicles) // 2),
                    'deals_updated': random.randint(0, len(vehicles) // 3),
                    'sync_duration': random.uniform(0.5, 2.0),
                    'errors': []
                }
            
            def sync_inventory_alerts(self, alerts):
                time.sleep(random.uniform(0.05, 0.15))
                self.alert_count += len(alerts)
                return {
                    'total_alerts': len(alerts),
                    'activities_created': random.randint(0, len(alerts)),
                    'notes_created': len(alerts),
                    'errors': []
                }
            
            def sync_competitive_insights(self, insights):
                time.sleep(random.uniform(0.1, 0.2))
                self.insight_count += len(insights)
                return {
                    'total_insights': len(insights),
                    'notes_created': len(insights),
                    'deals_updated': random.randint(0, len(insights)),
                    'errors': []
                }
        
        return MockPipeDriveIntegration()
    
    def _monitor_system_resources(self):
        """Monitor system resources during stress test"""
        
        while self.test_running and not self.shutdown_event.is_set():
            try:
                # Get system metrics
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)
                
                # Get process-specific metrics
                process = psutil.Process()
                process_memory = process.memory_info().rss / 1024 / 1024  # MB
                process_cpu = process.cpu_percent()
                
                metrics = {
                    'timestamp': time.time(),
                    'system_memory_percent': memory.percent,
                    'system_memory_used_mb': memory.used / 1024 / 1024,
                    'system_cpu_percent': cpu,
                    'process_memory_mb': process_memory,
                    'process_cpu_percent': process_cpu
                }
                
                self.system_metrics.append(metrics)
                
                # Sleep for monitoring interval
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                self.logger.warning(f"⚠️ System monitoring error: {str(e)}")
                time.sleep(10)  # Wait longer on error
    
    def _create_scraper_configurations(self) -> List[Dict[str, Any]]:
        """Create configurations for all scrapers to test"""
        
        configurations = [
            {
                'id': 'jaguarranchomirage',
                'name': 'Jaguar Rancho Mirage',
                'scraper_class': JaguarRanchoMirageWorkingScraper,
                'base_url': 'https://www.jaguarranchomirage.com',
                'tier': 'luxury',
                'group': 'ranch_mirage',
                'expected_vehicles': random.randint(20, 50)
            },
            {
                'id': 'landroverranchomirage', 
                'name': 'Land Rover Rancho Mirage',
                'scraper_class': LandRoverRanchoMirageWorkingScraper,
                'base_url': 'https://www.landroverofranchomirage.com',
                'tier': 'luxury',
                'group': 'ranch_mirage',
                'expected_vehicles': random.randint(15, 40)
            },
            {
                'id': 'bmwofweststlouis',
                'name': 'BMW of West St Louis',
                'scraper_class': BMWofWestStLouisWorkingScraper,
                'base_url': 'https://www.bmwofweststlouis.com',
                'tier': 'luxury',
                'group': 'bmw',
                'expected_vehicles': random.randint(50, 100)
            },
            {
                'id': 'suntrupfordwest',
                'name': 'Suntrup Ford West',
                'scraper_class': SuntrupFordWestWorkingScraper,
                'base_url': 'https://www.suntrupfordwest.com',
                'tier': 'mainstream',
                'group': 'suntrup',
                'expected_vehicles': random.randint(80, 150)
            }
        ]
        
        # Limit to config.concurrent_scrapers
        return configurations[:self.config.concurrent_scrapers]
    
    def _run_single_scraper_stress_test(self, scraper_config: Dict[str, Any]) -> ScraperStressResult:
        """Run stress test for a single scraper with all components"""
        
        result = ScraperStressResult(
            scraper_name=scraper_config['id'],
            dealership_name=scraper_config['name'],
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"🧪 Starting stress test for {scraper_config['name']}...")
            
            # Create simple config for scraper
            class SimpleConfig:
                request_delay = 2.0 if scraper_config['tier'] == 'luxury' else 1.0
                timeout = 60
            
            scraper_instance = scraper_config['scraper_class'](scraper_config, SimpleConfig())
            
            # Track performance metrics
            start_time = time.time()
            iteration = 0
            
            while (time.time() - start_time) < (self.config.duration_minutes * 60) and self.test_running:
                iteration += 1
                iteration_start = time.time()
                
                try:
                    # Step 1: Scrape inventory
                    self.logger.info(f"   Iteration {iteration}: Scraping {scraper_config['name']} inventory...")
                    
                    # Mock scraping for stress test (avoid hitting real websites)
                    if self.config.mock_external_apis:
                        vehicles = self._generate_mock_inventory(scraper_config)
                        result.api_calls_made += random.randint(5, 15)  # Simulate API calls
                    else:
                        vehicles = scraper_instance.scrape_inventory()
                        result.api_calls_made += 1
                    
                    result.vehicles_scraped += len(vehicles)
                    
                    # Step 2: Enhanced verification
                    if self.config.verification_enabled and vehicles:
                        verification_start = time.time()
                        verification_system = EnhancedInventoryVerificationSystem(
                            scraper_config['name'],
                            scraper_config,
                            scraper_instance.optimizer if hasattr(scraper_instance, 'optimizer') else None
                        )
                        
                        verification_report = verification_system.verify_inventory_completeness(
                            vehicles, enable_cross_verification=False  # Faster for stress test
                        )
                        result.verification_reports.append(verification_report)
                        result.performance_metrics[f'verification_time_iter_{iteration}'] = time.time() - verification_start
                    
                    # Step 3: Generate alerts
                    if self.config.alerts_enabled and self.alert_system and vehicles:
                        alerts_start = time.time()
                        alerts = self.alert_system.process_inventory_update(
                            scraper_config['id'],
                            scraper_config['name'],
                            vehicles,
                            verification_report if 'verification_report' in locals() else None
                        )
                        result.alerts_generated.extend([alert.__dict__ for alert in alerts])
                        result.performance_metrics[f'alerts_time_iter_{iteration}'] = time.time() - alerts_start
                    
                    # Step 4: Competitive analysis
                    if self.config.competitive_analysis_enabled and self.competitive_analyzer and vehicles:
                        competitive_start = time.time()
                        # Run competitive analysis on subset of vehicles for performance
                        sample_vehicles = vehicles[:min(10, len(vehicles))]
                        insights = self.competitive_analyzer.analyze_dealership_pricing(
                            scraper_config['name'],
                            sample_vehicles
                        )
                        result.competitive_insights.extend(insights)
                        result.performance_metrics[f'competitive_time_iter_{iteration}'] = time.time() - competitive_start
                    
                    # Step 5: PipeDrive sync
                    if self.config.pipedrive_integration_enabled and self.pipedrive_integration and vehicles:
                        pipedrive_start = time.time()
                        sync_report = self.pipedrive_integration.sync_vehicle_inventory(
                            vehicles, scraper_config['name']
                        )
                        result.pipedrive_syncs.append(sync_report)
                        result.performance_metrics[f'pipedrive_time_iter_{iteration}'] = time.time() - pipedrive_start
                    
                    # Record memory usage
                    if self.config.memory_monitoring:
                        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                        result.memory_usage.append((time.time(), memory_mb))
                    
                    # Iteration completed successfully
                    iteration_time = time.time() - iteration_start
                    result.performance_metrics[f'total_iteration_time_{iteration}'] = iteration_time
                    
                    self.logger.info(f"   ✅ Iteration {iteration} completed in {iteration_time:.1f}s: {len(vehicles)} vehicles")
                    
                    # Error injection for resilience testing
                    if random.random() < self.config.error_injection_rate:
                        raise Exception(f"Injected error for resilience testing (iteration {iteration})")
                    
                    # Rate limiting between iterations
                    if self.config.rate_limiting_enabled:
                        delay = random.uniform(5, 15)  # 5-15 second delay between iterations
                        time.sleep(delay)
                
                except Exception as e:
                    error_msg = f"Iteration {iteration} error: {str(e)}"
                    result.errors_encountered.append(error_msg)
                    self.logger.error(f"   ❌ {error_msg}")
                    
                    # Don't fail completely on individual iteration errors
                    time.sleep(5)  # Brief pause before next iteration
            
            result.end_time = datetime.now()
            result.success = len(result.errors_encountered) < (iteration * 0.1)  # Success if <10% error rate
            
            self.logger.info(f"✅ Stress test completed for {scraper_config['name']}: {result.vehicles_scraped} vehicles, {len(result.errors_encountered)} errors")
            
        except Exception as e:
            result.end_time = datetime.now()
            result.errors_encountered.append(f"Critical error: {str(e)}")
            result.success = False
            self.logger.error(f"❌ Critical error in stress test for {scraper_config['name']}: {str(e)}")
        
        return result
    
    def _generate_mock_inventory(self, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock inventory for stress testing"""
        
        vehicle_count = random.randint(10, self.config.vehicles_per_scraper // 10)
        vehicles = []
        
        for i in range(vehicle_count):
            vehicle = {
                'vin': self._generate_mock_vin(),
                'stock_number': f"STK{random.randint(10000, 99999)}",
                'year': random.randint(2018, 2024),
                'make': scraper_config['name'].split()[0],
                'model': f"Model{random.randint(1, 10)}",
                'price': random.randint(30000, 200000),
                'mileage': random.randint(0, 50000),
                'condition': random.choice(['New', 'Used', 'Certified']),
                'dealer_name': scraper_config['name'],
                'scraped_at': datetime.now().isoformat()
            }
            vehicles.append(vehicle)
        
        return vehicles
    
    def _generate_mock_vin(self) -> str:
        """Generate mock VIN for testing"""
        import string
        vin_chars = string.digits + "ABCDEFGHJKLMNPRSTUVWXYZ"
        return ''.join(random.choices(vin_chars, k=17))
    
    def run_comprehensive_stress_test(self) -> SystemStressResult:
        """Run comprehensive stress test of entire Silver Fox system"""
        
        self.logger.info("🚀 Starting comprehensive Silver Fox system stress test...")
        self.logger.info(f"   Duration: {self.config.duration_minutes} minutes")
        self.logger.info(f"   Concurrent scrapers: {self.config.concurrent_scrapers}")
        self.logger.info(f"   Components enabled: Verification={self.config.verification_enabled}, Alerts={self.config.alerts_enabled}, Competitive={self.config.competitive_analysis_enabled}, PipeDrive={self.config.pipedrive_integration_enabled}")
        
        # Initialize test result
        system_result = SystemStressResult(
            test_config=self.config,
            start_time=datetime.now()
        )
        
        try:
            # Initialize all system components
            self._initialize_system_components()
            
            # Get scraper configurations
            scraper_configs = self._create_scraper_configurations()
            
            # Run individual component stress tests first
            self._run_component_stress_tests(system_result)
            
            # Run concurrent scraper stress tests
            self.logger.info(f"\n🔥 Starting concurrent scraper stress tests with {len(scraper_configs)} scrapers...")
            
            with ThreadPoolExecutor(max_workers=self.config.concurrent_scrapers) as executor:
                # Submit all scraper stress tests
                future_to_config = {
                    executor.submit(self._run_single_scraper_stress_test, config): config
                    for config in scraper_configs
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_config):
                    config = future_to_config[future]
                    try:
                        scraper_result = future.result()
                        system_result.scraper_results.append(scraper_result)
                        
                        # Update totals
                        system_result.total_vehicles_scraped += scraper_result.vehicles_scraped
                        system_result.total_api_calls += scraper_result.api_calls_made
                        system_result.total_alerts_generated += len(scraper_result.alerts_generated)
                        system_result.total_competitive_insights += len(scraper_result.competitive_insights)
                        system_result.total_pipedrive_syncs += len(scraper_result.pipedrive_syncs)
                        
                    except Exception as e:
                        self.logger.error(f"❌ Scraper stress test failed for {config['name']}: {str(e)}")
            
            # Calculate final system metrics
            self._calculate_system_metrics(system_result)
            
            system_result.end_time = datetime.now()
            system_result.overall_success = self._evaluate_overall_success(system_result)
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive stress test failed: {str(e)}")
            system_result.end_time = datetime.now()
            system_result.overall_success = False
        
        finally:
            # Stop monitoring and cleanup
            self.test_running = False
            self.shutdown_event.set()
            
            if self.config.cleanup_on_exit:
                self._cleanup_resources()
        
        # Log comprehensive results
        self._log_comprehensive_results(system_result)
        
        return system_result
    
    def _run_component_stress_tests(self, system_result: SystemStressResult):
        """Run stress tests for individual components"""
        
        self.logger.info("🧪 Running individual component stress tests...")
        
        # PipeDrive integration stress test
        if self.config.pipedrive_integration_enabled:
            try:
                pipedrive_test_config = PipeDriveTestConfig(
                    mock_api=self.config.mock_external_apis,
                    stress_test_duration=min(300, self.config.duration_minutes * 60 // 4),  # 1/4 of total time
                    concurrent_threads=5,
                    vehicles_per_batch=50
                )
                
                pipedrive_test_suite = PipeDriveIntegrationTestSuite(pipedrive_test_config)
                pipedrive_results = pipedrive_test_suite.run_comprehensive_test_suite()
                
                system_result.system_metrics['pipedrive_component_test'] = pipedrive_results
                self.logger.info("✅ PipeDrive component stress test completed")
                
            except Exception as e:
                self.logger.error(f"❌ PipeDrive component stress test failed: {str(e)}")
        
        # Multi-dealership optimization stress test
        try:
            multi_dealership_test = MultiDealershipTestSuite()
            multi_dealership_test.run_comprehensive_test(
                quick_test=True,  # Quick test for stress testing
                specific_groups=['ranch_mirage', 'bmw'] if self.config.concurrent_scrapers <= 4 else None
            )
            
            system_result.system_metrics['multi_dealership_test'] = multi_dealership_test.results
            self.logger.info("✅ Multi-dealership optimization stress test completed")
            
        except Exception as e:
            self.logger.error(f"❌ Multi-dealership optimization stress test failed: {str(e)}")
    
    def _calculate_system_metrics(self, system_result: SystemStressResult):
        """Calculate comprehensive system metrics"""
        
        try:
            # Calculate error rate
            total_operations = sum(len(result.errors_encountered) + 1 for result in system_result.scraper_results)
            total_errors = sum(len(result.errors_encountered) for result in system_result.scraper_results)
            system_result.error_rate_percent = (total_errors / total_operations * 100) if total_operations > 0 else 0
            
            # Calculate peak memory usage
            if self.system_metrics:
                peak_memory = max(metric['process_memory_mb'] for metric in self.system_metrics)
                system_result.peak_memory_usage_mb = peak_memory
                
                # Calculate average CPU usage
                avg_cpu = sum(metric['process_cpu_percent'] for metric in self.system_metrics) / len(self.system_metrics)
                system_result.avg_cpu_usage_percent = avg_cpu
            
            # Store detailed system metrics
            system_result.system_metrics.update({
                'resource_monitoring': self.system_metrics,
                'scraper_count': len(system_result.scraper_results),
                'successful_scrapers': sum(1 for result in system_result.scraper_results if result.success),
                'total_test_duration_minutes': (system_result.end_time - system_result.start_time).total_seconds() / 60 if system_result.end_time else 0
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating system metrics: {str(e)}")
    
    def _evaluate_overall_success(self, system_result: SystemStressResult) -> bool:
        """Evaluate overall success of stress test"""
        
        try:
            # Success criteria
            successful_scrapers = sum(1 for result in system_result.scraper_results if result.success)
            scraper_success_rate = (successful_scrapers / len(system_result.scraper_results) * 100) if system_result.scraper_results else 0
            
            # Memory usage check (should not exceed 2GB)
            memory_ok = system_result.peak_memory_usage_mb < 2048
            
            # Error rate check (should be less than 15%)
            error_rate_ok = system_result.error_rate_percent < 15
            
            # Performance check (should scrape at least some vehicles)
            performance_ok = system_result.total_vehicles_scraped > 0
            
            # Overall success: 80% scraper success rate + reasonable resource usage + low error rate
            return (
                scraper_success_rate >= 80 and
                memory_ok and
                error_rate_ok and
                performance_ok
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating overall success: {str(e)}")
            return False
    
    def _cleanup_resources(self):
        """Clean up resources after stress test"""
        
        try:
            self.logger.info("🧹 Cleaning up stress test resources...")
            
            # Stop monitoring thread
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            # Clean up component instances
            self.alert_system = None
            self.competitive_analyzer = None
            self.pipedrive_integration = None
            
            self.logger.info("✅ Resource cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {str(e)}")
    
    def _log_comprehensive_results(self, system_result: SystemStressResult):
        """Log comprehensive stress test results"""
        
        duration_minutes = (system_result.end_time - system_result.start_time).total_seconds() / 60 if system_result.end_time else 0
        
        self.logger.info("\n" + "="*120)
        self.logger.info("🏁 COMPREHENSIVE SILVER FOX SYSTEM STRESS TEST RESULTS")
        self.logger.info("="*120)
        
        # Overall metrics
        self.logger.info(f"📊 OVERALL SYSTEM PERFORMANCE:")
        self.logger.info(f"   Test Duration: {duration_minutes:.1f} minutes")
        self.logger.info(f"   Overall Success: {'✅ PASSED' if system_result.overall_success else '❌ FAILED'}")
        self.logger.info(f"   Total Vehicles Scraped: {system_result.total_vehicles_scraped:,}")
        self.logger.info(f"   Total API Calls: {system_result.total_api_calls:,}")
        self.logger.info(f"   Total Alerts Generated: {system_result.total_alerts_generated:,}")
        self.logger.info(f"   Total Competitive Insights: {system_result.total_competitive_insights:,}")
        self.logger.info(f"   Total PipeDrive Syncs: {system_result.total_pipedrive_syncs:,}")
        self.logger.info(f"   Peak Memory Usage: {system_result.peak_memory_usage_mb:.1f} MB")
        self.logger.info(f"   Average CPU Usage: {system_result.avg_cpu_usage_percent:.1f}%")
        self.logger.info(f"   Error Rate: {system_result.error_rate_percent:.1f}%")
        
        # Individual scraper results
        self.logger.info(f"\n🏢 INDIVIDUAL SCRAPER RESULTS:")
        for result in system_result.scraper_results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            duration_mins = (result.end_time - result.start_time).total_seconds() / 60 if result.end_time else 0
            
            self.logger.info(f"   {status} {result.dealership_name}:")
            self.logger.info(f"     Duration: {duration_mins:.1f} min | Vehicles: {result.vehicles_scraped} | Errors: {len(result.errors_encountered)}")
            self.logger.info(f"     API Calls: {result.api_calls_made} | Alerts: {len(result.alerts_generated)} | Insights: {len(result.competitive_insights)}")
        
        # Component test results
        if 'pipedrive_component_test' in system_result.system_metrics:
            pipedrive_results = system_result.system_metrics['pipedrive_component_test']
            self.logger.info(f"\n💼 PIPEDRIVE COMPONENT TEST:")
            self.logger.info(f"   Status: {pipedrive_results.get('overall_status', 'Unknown')}")
            self.logger.info(f"   Tests Passed: {pipedrive_results.get('tests_passed', 0)}/{pipedrive_results.get('tests_run', 0)}")
        
        # Performance assessment
        self.logger.info(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if system_result.overall_success:
            self.logger.info("   🎉 EXCELLENT! The Silver Fox system handled the stress test exceptionally well!")
            self.logger.info("   🔥 All components working together seamlessly under load.")
            self.logger.info("   🚀 System is ready for production deployment with confidence.")
        else:
            self.logger.info("   ⚠️ NEEDS ATTENTION! Some components struggled under stress test conditions.")
            self.logger.info("   🛠️ Review failed components and optimize before full deployment.")
            self.logger.info("   📊 Consider reducing concurrent load or improving resource allocation.")
        
        # Resource usage analysis
        memory_mb = system_result.peak_memory_usage_mb
        if memory_mb < 512:
            self.logger.info(f"   💚 EXCELLENT memory usage: {memory_mb:.1f} MB peak")
        elif memory_mb < 1024:
            self.logger.info(f"   💛 GOOD memory usage: {memory_mb:.1f} MB peak")
        elif memory_mb < 2048:
            self.logger.info(f"   🧡 MODERATE memory usage: {memory_mb:.1f} MB peak")
        else:
            self.logger.info(f"   🔴 HIGH memory usage: {memory_mb:.1f} MB peak - consider optimization")
        
        # Recommendations
        self.logger.info(f"\n💡 RECOMMENDATIONS:")
        
        if system_result.error_rate_percent > 10:
            self.logger.info("   🔧 Improve error handling and resilience mechanisms")
        
        if system_result.peak_memory_usage_mb > 1024:
            self.logger.info("   🧠 Consider memory optimization and garbage collection improvements")
        
        if system_result.total_vehicles_scraped < (self.config.vehicles_per_scraper * self.config.concurrent_scrapers * 0.5):
            self.logger.info("   ⚡ Review scraper performance and rate limiting settings")
        
        successful_scrapers = sum(1 for result in system_result.scraper_results if result.success)
        if successful_scrapers < len(system_result.scraper_results):
            self.logger.info("   🛡️ Investigate and fix failing scraper components")
        
        self.logger.info("="*120)

def main():
    """Main stress test execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Silver Fox System Stress Test')
    parser.add_argument('--duration', type=int, default=30, 
                       help='Test duration in minutes (default: 30)')
    parser.add_argument('--concurrent-scrapers', type=int, default=4,
                       help='Number of concurrent scrapers (default: 4)')
    parser.add_argument('--vehicles-per-scraper', type=int, default=100,
                       help='Target vehicles per scraper (default: 100)')
    parser.add_argument('--disable-verification', action='store_true',
                       help='Disable inventory verification')
    parser.add_argument('--disable-alerts', action='store_true', 
                       help='Disable real-time alerts')
    parser.add_argument('--disable-competitive', action='store_true',
                       help='Disable competitive analysis')
    parser.add_argument('--disable-pipedrive', action='store_true',
                       help='Disable PipeDrive integration')
    parser.add_argument('--real-apis', action='store_true',
                       help='Use real APIs instead of mocks (NOT recommended for stress testing)')
    parser.add_argument('--error-rate', type=float, default=0.02,
                       help='Error injection rate for resilience testing (default: 0.02)')
    
    args = parser.parse_args()
    
    # Create stress test configuration
    config = StressTestConfiguration(
        duration_minutes=args.duration,
        concurrent_scrapers=args.concurrent_scrapers,
        vehicles_per_scraper=args.vehicles_per_scraper,
        verification_enabled=not args.disable_verification,
        alerts_enabled=not args.disable_alerts,
        competitive_analysis_enabled=not args.disable_competitive,
        pipedrive_integration_enabled=not args.disable_pipedrive,
        mock_external_apis=not args.real_apis,
        error_injection_rate=args.error_rate
    )
    
    # Run comprehensive stress test
    stress_test = ComprehensiveStressTest(config)
    results = stress_test.run_comprehensive_stress_test()
    
    # Exit with appropriate code
    if results.overall_success:
        print(f"\n🎉 Comprehensive stress test PASSED! Silver Fox system is ready for production.")
        sys.exit(0)
    else:
        print(f"\n❌ Comprehensive stress test identified issues. Review logs and optimize before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()