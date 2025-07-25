#!/usr/bin/env python3
"""
Silver Fox Stress Test Framework - Main System Interface
========================================================

Comprehensive stress testing framework for the Silver Fox scraper system.
Provides unified testing interface for performance validation, load testing,
and system reliability assessment.

Features:
- Individual scraper stress testing
- System-wide load testing
- Performance regression testing
- Concurrent execution testing
- Resource utilization monitoring
- Automated test reporting

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import time
import logging
import threading
import multiprocessing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import psutil
import traceback

# Add paths for accessing existing test modules
sys.path.insert(0, str(Path(__file__).parent / "silverfox_system" / "core" / "scrapers" / "tests"))
sys.path.insert(0, str(Path(__file__).parent / "tests"))

@dataclass
class StressTestResult:
    """Individual stress test result"""
    scraper_name: str
    test_type: str
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    vehicles_scraped: int
    avg_response_time: float
    peak_memory_mb: float
    cpu_usage_percent: float
    error_count: int
    errors: List[str]
    performance_score: float

@dataclass
class SystemStressResults:
    """System-wide stress test results"""
    test_session_id: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    scrapers_tested: int
    total_success_rate: float
    total_vehicles_scraped: int
    concurrent_peak: int
    system_resources: Dict[str, Any]
    individual_results: List[StressTestResult]
    performance_summary: Dict[str, Any]

class SilverFoxStressTestFramework:
    """
    Comprehensive stress testing framework for Silver Fox scraper system
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize stress test framework"""
        self.project_root = Path(__file__).parent
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Test session tracking
        self.session_id = f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results_dir = self.project_root / "stress_test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Load available test modules
        self.test_modules = self._discover_test_modules()
        
        # System monitoring
        self.system_monitor = SystemResourceMonitor()
        
        self.logger.info("✅ Silver Fox stress test framework initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load stress test configuration"""
        default_config = {
            'test_parameters': {
                'concurrent_scrapers': 5,
                'test_duration_minutes': 30,
                'iterations_per_scraper': 10,
                'timeout_seconds': 300,
                'memory_limit_mb': 1024,
                'cpu_limit_percent': 80
            },
            'test_types': {
                'individual_stress': {
                    'enabled': True,
                    'iterations': 10,
                    'concurrent_runs': 3
                },
                'system_load': {
                    'enabled': True,
                    'concurrent_scrapers': 10,
                    'duration_minutes': 15
                },
                'endurance_test': {
                    'enabled': False,
                    'duration_hours': 4,
                    'check_interval_minutes': 15
                },
                'resource_exhaustion': {
                    'enabled': True,
                    'memory_stress': True,
                    'cpu_stress': True
                }
            },
            'reporting': {
                'detailed_logs': True,
                'performance_graphs': False,
                'email_reports': False,
                'slack_notifications': False
            },
            'scrapers': {
                'priority_scrapers': [
                    'bmwofweststlouis_optimized',
                    'columbiabmw_optimized',
                    'jaguarranchomirage_optimized'
                ],
                'exclude_scrapers': [],
                'randomize_order': True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('stress_test_framework')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _discover_test_modules(self) -> Dict[str, Any]:
        """Discover available test modules"""
        modules = {}
        
        # Check for existing comprehensive stress test
        comprehensive_test_path = (
            self.project_root / "silverfox_system" / "core" / 
            "scrapers" / "tests" / "comprehensive_stress_test.py"
        )
        
        if comprehensive_test_path.exists():
            modules['comprehensive'] = {
                'path': comprehensive_test_path,
                'type': 'comprehensive',
                'available': True
            }
        
        # Check for individual scraper tests
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.glob("*stress*.py"):
                module_name = test_file.stem
                modules[module_name] = {
                    'path': test_file,
                    'type': 'individual',
                    'available': True
                }
        
        self.logger.info(f"📋 Discovered {len(modules)} test modules")
        return modules
    
    def run_comprehensive_stress_test(self) -> SystemStressResults:
        """Run comprehensive system stress test"""
        self.logger.info(f"🚀 Starting comprehensive stress test session: {self.session_id}")
        
        start_time = datetime.now()
        individual_results = []
        
        try:
            # Start system monitoring
            self.system_monitor.start_monitoring()
            
            # Get list of scrapers to test
            scrapers_to_test = self._get_scrapers_to_test()
            self.logger.info(f"📋 Testing {len(scrapers_to_test)} scrapers")
            
            # Run individual stress tests
            if self.config['test_types']['individual_stress']['enabled']:
                individual_results.extend(
                    self._run_individual_stress_tests(scrapers_to_test)
                )
            
            # Run system load test
            if self.config['test_types']['system_load']['enabled']:
                system_load_results = self._run_system_load_test(scrapers_to_test)
                individual_results.extend(system_load_results)
            
            # Run resource exhaustion test
            if self.config['test_types']['resource_exhaustion']['enabled']:
                resource_results = self._run_resource_exhaustion_test(scrapers_to_test)
                individual_results.extend(resource_results)
            
            # Stop system monitoring
            system_resources = self.system_monitor.stop_monitoring()
            
            # Calculate results
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # Create system results
            system_results = SystemStressResults(
                test_session_id=self.session_id,
                start_time=start_time,
                end_time=end_time,
                total_duration=total_duration,
                scrapers_tested=len(scrapers_to_test),
                total_success_rate=self._calculate_success_rate(individual_results),
                total_vehicles_scraped=sum(r.vehicles_scraped for r in individual_results),
                concurrent_peak=self.config['test_parameters']['concurrent_scrapers'],
                system_resources=system_resources,
                individual_results=individual_results,
                performance_summary=self._create_performance_summary(individual_results)
            )
            
            # Save results
            self._save_test_results(system_results)
            
            # Generate report
            self._generate_test_report(system_results)
            
            self.logger.info("✅ Comprehensive stress test completed")
            return system_results
            
        except Exception as e:
            self.logger.error(f"❌ Stress test failed: {e}")
            self.system_monitor.stop_monitoring()
            raise
    
    def _get_scrapers_to_test(self) -> List[str]:
        """Get list of scrapers to test"""
        scrapers_dir = self.project_root / "silverfox_system" / "core" / "scrapers" / "dealerships"
        
        # Get all optimized scrapers
        all_scrapers = [
            f.stem for f in scrapers_dir.glob("*_optimized.py")
        ]
        
        # Filter based on configuration
        priority_scrapers = self.config['scrapers']['priority_scrapers']
        exclude_scrapers = self.config['scrapers']['exclude_scrapers']
        
        if priority_scrapers:
            # Use priority scrapers if specified
            scrapers_to_test = [s for s in priority_scrapers if s in all_scrapers]
        else:
            # Use all scrapers
            scrapers_to_test = all_scrapers
        
        # Remove excluded scrapers
        scrapers_to_test = [s for s in scrapers_to_test if s not in exclude_scrapers]
        
        # Randomize order if configured
        if self.config['scrapers']['randomize_order']:
            import random
            random.shuffle(scrapers_to_test)
        
        return scrapers_to_test
    
    def _run_individual_stress_tests(self, scrapers: List[str]) -> List[StressTestResult]:
        """Run individual scraper stress tests"""
        self.logger.info("🔧 Running individual scraper stress tests")
        
        results = []
        test_config = self.config['test_types']['individual_stress']
        
        for scraper_name in scrapers:
            self.logger.info(f"🧪 Testing {scraper_name}")
            
            # Run multiple iterations for this scraper
            scraper_results = []
            
            for iteration in range(test_config['iterations']):
                result = self._run_single_scraper_test(
                    scraper_name, 
                    f"individual_iteration_{iteration + 1}"
                )
                if result:
                    scraper_results.append(result)
            
            # Calculate average performance for this scraper
            if scraper_results:
                avg_result = self._aggregate_scraper_results(scraper_name, scraper_results)
                results.append(avg_result)
        
        return results
    
    def _run_system_load_test(self, scrapers: List[str]) -> List[StressTestResult]:
        """Run system-wide load test with concurrent scrapers"""
        self.logger.info("⚡ Running system load test")
        
        results = []
        test_config = self.config['test_types']['system_load']
        concurrent_limit = test_config['concurrent_scrapers']
        
        # Select scrapers for concurrent testing
        test_scrapers = scrapers[:concurrent_limit]
        
        # Run scrapers concurrently
        with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
            # Submit all scraper tests
            future_to_scraper = {
                executor.submit(
                    self._run_single_scraper_test, 
                    scraper_name, 
                    "system_load_test"
                ): scraper_name 
                for scraper_name in test_scrapers
            }
            
            # Collect results
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    result = future.result(timeout=self.config['test_parameters']['timeout_seconds'])
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ System load test failed for {scraper_name}: {e}")
                    # Create failure result
                    failure_result = StressTestResult(
                        scraper_name=scraper_name,
                        test_type="system_load_test",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration=0,
                        success=False,
                        vehicles_scraped=0,
                        avg_response_time=0,
                        peak_memory_mb=0,
                        cpu_usage_percent=0,
                        error_count=1,
                        errors=[str(e)],
                        performance_score=0
                    )
                    results.append(failure_result)
        
        return results
    
    def _run_resource_exhaustion_test(self, scrapers: List[str]) -> List[StressTestResult]:
        """Run resource exhaustion test"""
        self.logger.info("💾 Running resource exhaustion test")
        
        results = []
        
        # Test with limited memory
        if self.config['test_types']['resource_exhaustion']['memory_stress']:
            memory_results = self._run_memory_stress_test(scrapers[:3])  # Test first 3 scrapers
            results.extend(memory_results)
        
        # Test with high CPU load
        if self.config['test_types']['resource_exhaustion']['cpu_stress']:
            cpu_results = self._run_cpu_stress_test(scrapers[:3])
            results.extend(cpu_results)
        
        return results
    
    def _run_single_scraper_test(self, scraper_name: str, test_type: str) -> Optional[StressTestResult]:
        """Run stress test on a single scraper"""
        start_time = datetime.now()
        
        try:
            # Import scraper dynamically
            scraper = self._import_scraper(scraper_name)
            if not scraper:
                return None
            
            # Monitor resources during test
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            peak_memory = initial_memory
            
            # Run scraper
            vehicles = scraper.get_all_vehicles()
            
            # Collect metrics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            final_memory = process.memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, final_memory)
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(
                duration, len(vehicles) if vehicles else 0, peak_memory
            )
            
            return StressTestResult(
                scraper_name=scraper_name,
                test_type=test_type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=vehicles is not None and len(vehicles) > 0,
                vehicles_scraped=len(vehicles) if vehicles else 0,
                avg_response_time=duration,
                peak_memory_mb=peak_memory,
                cpu_usage_percent=process.cpu_percent(),
                error_count=0,
                errors=[],
                performance_score=performance_score
            )
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(f"❌ Test failed for {scraper_name}: {e}")
            
            return StressTestResult(
                scraper_name=scraper_name,
                test_type=test_type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=False,
                vehicles_scraped=0,
                avg_response_time=duration,
                peak_memory_mb=0,
                cpu_usage_percent=0,
                error_count=1,
                errors=[str(e)],
                performance_score=0
            )
    
    def _import_scraper(self, scraper_name: str):
        """Dynamically import scraper class"""
        try:
            scraper_path = (
                self.project_root / "silverfox_system" / "core" / 
                "scrapers" / "dealerships" / f"{scraper_name}.py"
            )
            
            if not scraper_path.exists():
                self.logger.warning(f"⚠️ Scraper not found: {scraper_path}")
                return None
            
            # Dynamic import
            import importlib.util
            spec = importlib.util.spec_from_file_location(scraper_name, scraper_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find scraper class
            scraper_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('OptimizedScraper') and 
                    hasattr(attr, 'get_all_vehicles')):
                    scraper_class = attr
                    break
            
            if scraper_class:
                return scraper_class()
            else:
                self.logger.warning(f"⚠️ No scraper class found in {scraper_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to import scraper {scraper_name}: {e}")
            return None
    
    def _run_memory_stress_test(self, scrapers: List[str]) -> List[StressTestResult]:
        """Run scrapers under memory pressure"""
        self.logger.info("💾 Running memory stress test")
        
        results = []
        
        # Create memory pressure (allocate large chunks of memory)
        memory_hog = []
        try:
            # Allocate ~500MB of memory
            for _ in range(50):
                memory_hog.append(b'x' * (10 * 1024 * 1024))  # 10MB chunks
            
            # Run scrapers under memory pressure
            for scraper_name in scrapers:
                result = self._run_single_scraper_test(scraper_name, "memory_stress")
                if result:
                    results.append(result)
                    
        finally:
            # Clean up memory
            del memory_hog
        
        return results
    
    def _run_cpu_stress_test(self, scrapers: List[str]) -> List[StressTestResult]:
        """Run scrapers under CPU pressure"""
        self.logger.info("⚡ Running CPU stress test")
        
        results = []
        
        # Create CPU stress using background threads
        cpu_stress_active = threading.Event()
        cpu_stress_active.set()
        
        def cpu_stress_worker():
            """Background CPU stress worker"""
            while cpu_stress_active.is_set():
                # Perform CPU-intensive operation
                sum(i * i for i in range(10000))
        
        # Start CPU stress threads
        stress_threads = []
        for _ in range(multiprocessing.cpu_count()):
            thread = threading.Thread(target=cpu_stress_worker, daemon=True)
            thread.start()
            stress_threads.append(thread)
        
        try:
            # Run scrapers under CPU pressure
            for scraper_name in scrapers:
                result = self._run_single_scraper_test(scraper_name, "cpu_stress")
                if result:
                    results.append(result)
                    
        finally:
            # Stop CPU stress
            cpu_stress_active.clear()
            for thread in stress_threads:
                thread.join(timeout=1)
        
        return results
    
    def _aggregate_scraper_results(self, scraper_name: str, results: List[StressTestResult]) -> StressTestResult:
        """Aggregate multiple test results for a scraper"""
        if not results:
            return None
        
        total_duration = sum(r.duration for r in results)
        total_vehicles = sum(r.vehicles_scraped for r in results)
        success_count = sum(1 for r in results if r.success)
        
        return StressTestResult(
            scraper_name=scraper_name,
            test_type="individual_aggregated",
            start_time=min(r.start_time for r in results),
            end_time=max(r.end_time for r in results),
            duration=total_duration / len(results),  # Average duration
            success=success_count > len(results) / 2,  # Majority success
            vehicles_scraped=total_vehicles // len(results),  # Average vehicles
            avg_response_time=total_duration / len(results),
            peak_memory_mb=max(r.peak_memory_mb for r in results),
            cpu_usage_percent=sum(r.cpu_usage_percent for r in results) / len(results),
            error_count=sum(r.error_count for r in results),
            errors=[error for r in results for error in r.errors],
            performance_score=sum(r.performance_score for r in results) / len(results)
        )
    
    def _calculate_performance_score(self, duration: float, vehicles: int, memory_mb: float) -> float:
        """Calculate performance score (0-100)"""
        # Base score factors
        speed_score = max(0, 100 - (duration * 2))  # Penalty for slow execution
        efficiency_score = min(100, vehicles * 2)   # Reward for more vehicles
        memory_score = max(0, 100 - (memory_mb / 10))  # Penalty for high memory usage
        
        # Weighted average
        performance_score = (speed_score * 0.4 + efficiency_score * 0.4 + memory_score * 0.2)
        return min(100, max(0, performance_score))
    
    def _calculate_success_rate(self, results: List[StressTestResult]) -> float:
        """Calculate overall success rate"""
        if not results:
            return 0.0
        
        successful = sum(1 for r in results if r.success)
        return successful / len(results) * 100
    
    def _create_performance_summary(self, results: List[StressTestResult]) -> Dict[str, Any]:
        """Create performance summary statistics"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        
        return {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'success_rate': len(successful_results) / len(results) * 100,
            'avg_duration': sum(r.duration for r in successful_results) / len(successful_results) if successful_results else 0,
            'avg_vehicles_per_test': sum(r.vehicles_scraped for r in successful_results) / len(successful_results) if successful_results else 0,
            'avg_performance_score': sum(r.performance_score for r in successful_results) / len(successful_results) if successful_results else 0,
            'peak_memory_usage': max(r.peak_memory_mb for r in results) if results else 0,
            'total_errors': sum(r.error_count for r in results),
            'fastest_scraper': min(successful_results, key=lambda x: x.duration).scraper_name if successful_results else None,
            'most_efficient_scraper': max(successful_results, key=lambda x: x.vehicles_scraped).scraper_name if successful_results else None
        }
    
    def _save_test_results(self, results: SystemStressResults):
        """Save test results to file"""
        try:
            results_file = self.results_dir / f"{self.session_id}_results.json"
            
            # Convert to JSON-serializable format
            results_dict = asdict(results)
            
            with open(results_file, 'w') as f:
                json.dump(results_dict, f, indent=2, default=str)
            
            self.logger.info(f"📄 Test results saved: {results_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save test results: {e}")
    
    def _generate_test_report(self, results: SystemStressResults):
        """Generate human-readable test report"""
        try:
            report_file = self.results_dir / f"{self.session_id}_report.txt"
            
            with open(report_file, 'w') as f:
                f.write("SILVER FOX SCRAPER SYSTEM - STRESS TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Test Session: {results.test_session_id}\n")
                f.write(f"Duration: {results.total_duration:.2f} seconds\n")
                f.write(f"Scrapers Tested: {results.scrapers_tested}\n")
                f.write(f"Success Rate: {results.total_success_rate:.1f}%\n")
                f.write(f"Total Vehicles Scraped: {results.total_vehicles_scraped:,}\n\n")
                
                f.write("PERFORMANCE SUMMARY:\n")
                f.write("-" * 30 + "\n")
                summary = results.performance_summary
                for key, value in summary.items():
                    f.write(f"{key.title().replace('_', ' ')}: {value}\n")
                
                f.write("\nINDIVIDUAL SCRAPER RESULTS:\n")
                f.write("-" * 40 + "\n")
                
                for result in results.individual_results:
                    status = "✅ PASS" if result.success else "❌ FAIL"
                    f.write(f"{status} {result.scraper_name}\n")
                    f.write(f"  Duration: {result.duration:.2f}s\n")
                    f.write(f"  Vehicles: {result.vehicles_scraped}\n")
                    f.write(f"  Performance Score: {result.performance_score:.1f}/100\n")
                    if result.errors:
                        f.write(f"  Errors: {', '.join(result.errors[:3])}\n")
                    f.write("\n")
            
            self.logger.info(f"📋 Test report generated: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate test report: {e}")
    
    def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation test on priority scrapers"""
        self.logger.info("⚡ Running quick validation test")
        
        priority_scrapers = self.config['scrapers']['priority_scrapers'][:3]  # Test top 3
        results = []
        
        for scraper_name in priority_scrapers:
            result = self._run_single_scraper_test(scraper_name, "quick_validation")
            if result:
                results.append(result)
        
        success_rate = self._calculate_success_rate(results)
        
        return {
            'test_type': 'quick_validation',
            'scrapers_tested': len(priority_scrapers),
            'success_rate': success_rate,
            'results': [asdict(r) for r in results],
            'status': 'pass' if success_rate > 80 else 'fail'
        }


class SystemResourceMonitor:
    """Monitor system resources during stress testing"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return summary"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if not self.metrics:
            return {}
        
        # Calculate summary statistics
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        
        return {
            'monitoring_duration': len(self.metrics) * 5,  # 5-second intervals
            'cpu_usage': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'sample_count': len(self.metrics)
        }
    
    def _monitor_loop(self):
        """Monitor system resources"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                self.metrics.append({
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3)
                })
                
                time.sleep(5)  # Sample every 5 seconds
                
            except Exception:
                pass  # Continue monitoring despite errors


def main():
    """Main execution for command-line usage"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Silver Fox Stress Test Framework')
    parser.add_argument('--full', action='store_true', help='Run full comprehensive stress test')
    parser.add_argument('--quick', action='store_true', help='Run quick validation test')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--scrapers', nargs='+', help='Specific scrapers to test')
    
    args = parser.parse_args()
    
    print("🧪 Silver Fox Stress Test Framework")
    print("=" * 40)
    
    # Initialize framework
    framework = SilverFoxStressTestFramework(args.config)
    
    if args.quick:
        print("⚡ Running quick validation test...")
        results = framework.run_quick_validation()
        print(f"✅ Test completed: {results['success_rate']:.1f}% success rate")
        print(f"Status: {results['status'].upper()}")
        
    elif args.full:
        print("🚀 Running comprehensive stress test...")
        results = framework.run_comprehensive_stress_test()
        print(f"✅ Test completed: {results.total_success_rate:.1f}% success rate")
        print(f"Vehicles scraped: {results.total_vehicles_scraped:,}")
        print(f"Duration: {results.total_duration:.1f} seconds")
        
    else:
        print("📊 Available test options:")
        print("  --quick : Quick validation test")
        print("  --full  : Comprehensive stress test")
        print("  --config <path> : Use custom configuration")


if __name__ == "__main__":
    main()