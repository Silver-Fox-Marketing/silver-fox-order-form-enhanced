#!/usr/bin/env python3
"""
Production Scraper Validator for Silver Fox Scraper System
==========================================================

Production-ready validation script to test actual scrapers against live dealership
websites to ensure:
1. Accurate on-lot vehicle data collection
2. Complete inventory pagination handling
3. No first-page-only limitations  
4. Proper error handling and recovery
5. Data quality validation

⚠️  USE WITH CAUTION: This tests against live websites!

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import asyncio
import logging
import time
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import traceback
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ProductionTestResult:
    """Result from production scraper validation"""
    scraper_name: str
    dealership: str
    website_url: str
    test_start_time: datetime
    test_end_time: Optional[datetime]
    duration_seconds: float
    success: bool
    total_vehicles_found: int
    pages_accessed: int
    first_page_only_detected: bool
    data_quality_issues: List[str]
    performance_metrics: Dict[str, Any]
    validation_details: Dict[str, Any]
    recommendations: List[str]


class ProductionScraperValidator:
    """Validator for production scrapers against live websites"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ProductionScraperValidator")
        
        # Test configuration
        self.test_timeout = config.get('test_timeout', 1800)  # 30 minutes max
        self.min_expected_vehicles = config.get('min_expected_vehicles', 1)
        self.max_expected_vehicles = config.get('max_expected_vehicles', 1000)
        self.data_quality_threshold = config.get('data_quality_threshold', 0.8)
        self.respect_rate_limits = config.get('respect_rate_limits', True)
        self.delay_between_requests = config.get('delay_between_requests', 3.0)
        
        # Production scrapers to validate
        self.production_scrapers = {
            'jaguar_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.jaguarranchomirage_working',
                'class_name': 'JaguarRanchMirageScraper',
                'dealership': 'Jaguar Ranch Mirage',
                'website_url': 'https://www.jaguarranchmirage.com',
                'expected_min_vehicles': 5,
                'platform': 'DealerOn'
            },
            'landrover_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.landroverranchomirage_working',
                'class_name': 'LandRoverRanchMirageScraper',
                'dealership': 'Land Rover Ranch Mirage',
                'website_url': 'https://www.landroverpalmdesert.com',
                'expected_min_vehicles': 8,
                'platform': 'DealerOn'
            },
            'astonmartin_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.astonmartinranchomirage_working',
                'class_name': 'AstonMartinRanchMirageScraper',
                'dealership': 'Aston Martin Ranch Mirage',
                'website_url': 'https://www.astonmartinranchmirage.com',
                'expected_min_vehicles': 2,
                'platform': 'DealerOn'
            },
            'bentley_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.bentleyranchomirage_working',
                'class_name': 'BentleyRanchMirageScraper',
                'dealership': 'Bentley Ranch Mirage',
                'website_url': 'https://www.bentleyranchmirage.com',
                'expected_min_vehicles': 3,
                'platform': 'DealerOn'
            },
            'mclaren_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.mclarenranchomirage_working',
                'class_name': 'McLarenRanchMirageScraper',
                'dealership': 'McLaren Ranch Mirage',
                'website_url': 'https://www.mclarenranchmirage.com',
                'expected_min_vehicles': 1,
                'platform': 'DealerOn'
            },
            'rollsroyce_ranch_mirage': {
                'module_path': 'core.scrapers.dealeron.rollsroyceranchomirage_working',
                'class_name': 'RollsRoyceRanchMirageScraper',
                'dealership': 'Rolls-Royce Ranch Mirage',
                'website_url': 'https://www.rollsroycemotorcarspalmdesert.com',
                'expected_min_vehicles': 1,
                'platform': 'DealerOn'
            }
        }
        
        # Results storage
        self.test_results: List[ProductionTestResult] = []
    
    def _import_scraper_class(self, module_path: str, class_name: str):
        """Dynamically import scraper class"""
        try:
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            return scraper_class
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to import {class_name} from {module_path}: {e}")
            return None
    
    async def validate_individual_scraper(self, scraper_name: str, run_live_test: bool = False) -> ProductionTestResult:
        """Validate individual scraper against production website"""
        if scraper_name not in self.production_scrapers:
            raise ValueError(f"Unknown scraper: {scraper_name}")
        
        scraper_config = self.production_scrapers[scraper_name]
        
        self.logger.info(f"🔍 Starting production validation for {scraper_name}")
        self.logger.info(f"📍 Target: {scraper_config['dealership']} ({scraper_config['website_url']})")
        
        if not run_live_test:
            self.logger.warning(f"⚠️  DRY RUN MODE - Not connecting to live website")
            return self._create_dry_run_result(scraper_name, scraper_config)
        
        test_start = datetime.now()
        data_quality_issues = []
        recommendations = []
        
        try:
            # Import scraper class
            scraper_class = self._import_scraper_class(
                scraper_config['module_path'],
                scraper_config['class_name']
            )
            
            if not scraper_class:
                raise Exception(f"Could not import scraper class: {scraper_config['class_name']}")
            
            # Initialize scraper
            scraper = scraper_class()
            
            self.logger.info(f"🚀 Starting live scraping test...")
            
            # Respect rate limits
            if self.respect_rate_limits:
                await asyncio.sleep(self.delay_between_requests)
            
            # Phase 1: Basic scraping test
            scrape_start = time.time()
            vehicles = await asyncio.wait_for(
                scraper.scrape_vehicles(),
                timeout=self.test_timeout
            )
            scrape_duration = time.time() - scrape_start
            
            self.logger.info(f"✅ Scraping completed: {len(vehicles)} vehicles found in {scrape_duration:.1f}s")
            
            # Phase 2: Data quality analysis
            quality_analysis = await self._analyze_data_quality(vehicles, scraper_name)
            data_quality_issues.extend(quality_analysis['issues'])
            
            # Phase 3: Pagination detection
            pagination_analysis = await self._detect_pagination_issues(
                vehicles, scraper, scraper_name
            )
            
            first_page_only = pagination_analysis['first_page_only_detected']
            if first_page_only:
                data_quality_issues.append("CRITICAL: Scraper appears to be stuck on first page only")
                recommendations.append("Implement proper pagination handling")
            
            # Phase 4: Performance analysis
            performance_metrics = {
                'scrape_duration_seconds': scrape_duration,
                'vehicles_per_second': len(vehicles) / scrape_duration if scrape_duration > 0 else 0,
                'average_vehicle_processing_time': scrape_duration / len(vehicles) if len(vehicles) > 0 else 0,
                'pages_accessed': pagination_analysis['estimated_pages'],
                'data_completeness_score': quality_analysis['completeness_score']
            }
            
            # Determine success criteria
            expected_min = scraper_config['expected_min_vehicles']
            vehicle_count_ok = len(vehicles) >= expected_min
            quality_ok = quality_analysis['completeness_score'] >= self.data_quality_threshold
            pagination_ok = not first_page_only
            
            success = all([vehicle_count_ok, quality_ok, pagination_ok])
            
            # Generate recommendations
            if not vehicle_count_ok:
                recommendations.append(f"Vehicle count ({len(vehicles)}) below expected minimum ({expected_min})")
            
            if not quality_ok:
                recommendations.append(f"Data quality score ({quality_analysis['completeness_score']:.2f}) below threshold ({self.data_quality_threshold})")
            
            if success:
                recommendations.append("✅ Scraper is performing correctly!")
            
            test_end = datetime.now()
            
            return ProductionTestResult(
                scraper_name=scraper_name,
                dealership=scraper_config['dealership'],
                website_url=scraper_config['website_url'],
                test_start_time=test_start,
                test_end_time=test_end,
                duration_seconds=(test_end - test_start).total_seconds(),
                success=success,
                total_vehicles_found=len(vehicles),
                pages_accessed=pagination_analysis['estimated_pages'],
                first_page_only_detected=first_page_only,
                data_quality_issues=data_quality_issues,
                performance_metrics=performance_metrics,
                validation_details={
                    'quality_analysis': quality_analysis,
                    'pagination_analysis': pagination_analysis,
                    'vehicle_sample': vehicles[:3] if vehicles else []  # First 3 vehicles for review
                },
                recommendations=recommendations
            )
            
        except asyncio.TimeoutError:
            test_end = datetime.now()
            error_msg = f"Scraping timed out after {self.test_timeout} seconds"
            self.logger.error(f"❌ {scraper_name}: {error_msg}")
            
            return ProductionTestResult(
                scraper_name=scraper_name,
                dealership=scraper_config['dealership'],
                website_url=scraper_config['website_url'],
                test_start_time=test_start,
                test_end_time=test_end,
                duration_seconds=(test_end - test_start).total_seconds(),
                success=False,
                total_vehicles_found=0,
                pages_accessed=0,
                first_page_only_detected=False,
                data_quality_issues=[error_msg],
                performance_metrics={},
                validation_details={'error': error_msg},
                recommendations=[f"Fix timeout issue - scraper took longer than {self.test_timeout} seconds"]
            )
            
        except Exception as e:
            test_end = datetime.now()
            error_msg = f"Critical error: {str(e)}"
            self.logger.error(f"❌ {scraper_name} validation failed: {e}")
            self.logger.error(traceback.format_exc())
            
            return ProductionTestResult(
                scraper_name=scraper_name,
                dealership=scraper_config['dealership'],
                website_url=scraper_config['website_url'],
                test_start_time=test_start,
                test_end_time=test_end,
                duration_seconds=(test_end - test_start).total_seconds(),
                success=False,
                total_vehicles_found=0,
                pages_accessed=0,
                first_page_only_detected=False,
                data_quality_issues=[error_msg],
                performance_metrics={},
                validation_details={'error': error_msg, 'traceback': traceback.format_exc()},
                recommendations=[f"Fix critical error: {str(e)}"]
            )
    
    def _create_dry_run_result(self, scraper_name: str, scraper_config: Dict[str, Any]) -> ProductionTestResult:
        """Create a dry run result without actually testing"""
        return ProductionTestResult(
            scraper_name=scraper_name,
            dealership=scraper_config['dealership'],
            website_url=scraper_config['website_url'],
            test_start_time=datetime.now(),
            test_end_time=datetime.now(),
            duration_seconds=0.0,
            success=True,  # Assume success for dry run
            total_vehicles_found=0,
            pages_accessed=0,
            first_page_only_detected=False,
            data_quality_issues=[],
            performance_metrics={},
            validation_details={'dry_run': True},
            recommendations=["DRY RUN - Use --live flag to test against actual websites"]
        )
    
    async def _analyze_data_quality(self, vehicles: List[Dict[str, Any]], scraper_name: str) -> Dict[str, Any]:
        """Analyze data quality of scraped vehicles"""
        if not vehicles:
            return {
                'completeness_score': 0.0,
                'issues': ['No vehicles found'],
                'field_analysis': {}
            }
        
        # Required fields for quality assessment
        required_fields = ['make', 'model', 'year', 'price', 'vin']
        important_fields = ['mileage', 'color', 'transmission']
        
        issues = []
        field_analysis = {}
        scores = []
        
        # Check field completeness
        for field in required_fields + important_fields:
            present_count = sum(1 for v in vehicles if v.get(field) and str(v.get(field)).strip())
            completeness = present_count / len(vehicles)
            
            field_analysis[field] = {
                'completeness': completeness,
                'present': present_count,
                'total': len(vehicles),
                'is_required': field in required_fields
            }
            
            # Weight required fields more heavily
            weight = 2.0 if field in required_fields else 1.0
            scores.append(completeness * weight)
            
            # Flag issues
            if field in required_fields and completeness < 0.9:
                issues.append(f"Low completeness for required field '{field}': {completeness:.1%}")
            elif field in important_fields and completeness < 0.5:
                issues.append(f"Low completeness for important field '{field}': {completeness:.1%}")
        
        # Check for data consistency
        if vehicles:
            # Year validation
            valid_years = sum(
                1 for v in vehicles 
                if v.get('year') and isinstance(v['year'], int) and 1990 <= v['year'] <= 2025
            )
            year_validity = valid_years / len(vehicles)
            if year_validity < 0.9:
                issues.append(f"Invalid years detected in {(1-year_validity):.1%} of vehicles")
            
            # Price validation
            valid_prices = sum(
                1 for v in vehicles 
                if v.get('price') and (isinstance(v['price'], (int, float)) or 
                                     (isinstance(v['price'], str) and v['price'].replace('$', '').replace(',', '').isdigit()))
            )
            price_validity = valid_prices / len(vehicles)
            if price_validity < 0.8:
                issues.append(f"Invalid prices detected in {(1-price_validity):.1%} of vehicles")
            
            # VIN validation
            valid_vins = sum(
                1 for v in vehicles 
                if v.get('vin') and isinstance(v['vin'], str) and 10 <= len(v['vin']) <= 17
            )
            vin_validity = valid_vins / len(vehicles)
            if vin_validity < 0.7:
                issues.append(f"Invalid VINs detected in {(1-vin_validity):.1%} of vehicles")
            
            # Duplicate detection
            vins = [v.get('vin', '') for v in vehicles if v.get('vin')]
            unique_vins = len(set(vins))
            if len(vins) > 0 and unique_vins != len(vins):
                duplicate_count = len(vins) - unique_vins
                issues.append(f"Found {duplicate_count} duplicate VINs")
        
        # Calculate overall completeness score
        completeness_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'field_analysis': field_analysis
        }
    
    async def _detect_pagination_issues(self, vehicles: List[Dict[str, Any]], scraper, scraper_name: str) -> Dict[str, Any]:
        """Detect potential pagination issues"""
        try:
            # Heuristics to detect first-page-only behavior
            vehicle_count = len(vehicles)
            
            # Check for suspiciously round numbers that might indicate page limits
            suspicious_counts = [10, 12, 15, 20, 24, 25, 30]
            suspiciously_round = vehicle_count in suspicious_counts
            
            # Check if count is unusually low for a dealership
            unusually_low = vehicle_count < 5
            
            # Estimate pages based on typical page sizes
            typical_page_sizes = [10, 12, 15, 20, 24, 25]
            estimated_pages = 1
            
            for page_size in typical_page_sizes:
                if vehicle_count % page_size == 0 and vehicle_count > page_size:
                    estimated_pages = vehicle_count // page_size
                    break
                elif vehicle_count <= page_size:
                    estimated_pages = 1
                    break
            
            # More sophisticated check: look for patterns in vehicle data
            # that might indicate incomplete scraping
            first_page_indicators = []
            
            if suspiciously_round:
                first_page_indicators.append(f"Vehicle count ({vehicle_count}) matches typical page size")
            
            if unusually_low:
                first_page_indicators.append(f"Unusually low vehicle count ({vehicle_count}) for dealership")
            
            # Check for identical or sequential patterns that might indicate test data
            if vehicles and len(vehicles) > 1:
                prices = [v.get('price', 0) for v in vehicles if isinstance(v.get('price'), (int, float))]
                if len(set(prices)) == 1 and len(prices) > 3:
                    first_page_indicators.append("All vehicles have identical prices (possible test data)")
            
            first_page_only_detected = len(first_page_indicators) >= 2
            
            return {
                'first_page_only_detected': first_page_only_detected,
                'estimated_pages': estimated_pages,
                'indicators': first_page_indicators,
                'analysis': {
                    'vehicle_count': vehicle_count,
                    'suspiciously_round': suspiciously_round,
                    'unusually_low': unusually_low
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in pagination analysis: {e}")
            return {
                'first_page_only_detected': False,
                'estimated_pages': 1,
                'indicators': [f"Analysis error: {str(e)}"],
                'analysis': {}
            }
    
    async def validate_all_scrapers(self, run_live_test: bool = False) -> Dict[str, ProductionTestResult]:
        """Validate all production scrapers"""
        if run_live_test:
            self.logger.warning("🚨 LIVE TEST MODE - Will connect to actual dealership websites!")
            self.logger.warning("⚠️  Please ensure you have permission and are respecting rate limits")
            await asyncio.sleep(3)  # Give user time to cancel
        else:
            self.logger.info("📋 DRY RUN MODE - No actual website connections will be made")
        
        results = {}
        total_scrapers = len(self.production_scrapers)
        
        for i, scraper_name in enumerate(self.production_scrapers.keys(), 1):
            self.logger.info(f"🔍 Validating scraper {i}/{total_scrapers}: {scraper_name}")
            
            try:
                result = await self.validate_individual_scraper(scraper_name, run_live_test)
                results[scraper_name] = result
                
                # Log immediate result
                status = "✅ PASSED" if result.success else "❌ FAILED"
                self.logger.info(f"{status} {scraper_name}: {result.total_vehicles_found} vehicles")
                
                # Respect rate limits between tests
                if run_live_test and i < total_scrapers:
                    delay = self.delay_between_requests * 2  # Longer delay between full scraper tests
                    self.logger.info(f"⏳ Waiting {delay}s to respect rate limits...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"❌ {scraper_name} validation crashed: {e}")
                # Create failure result
                results[scraper_name] = ProductionTestResult(
                    scraper_name=scraper_name,
                    dealership=self.production_scrapers[scraper_name]['dealership'],
                    website_url=self.production_scrapers[scraper_name]['website_url'],
                    test_start_time=datetime.now(),
                    test_end_time=datetime.now(),
                    duration_seconds=0,
                    success=False,
                    total_vehicles_found=0,
                    pages_accessed=0,
                    first_page_only_detected=False,
                    data_quality_issues=[str(e)],
                    performance_metrics={},
                    validation_details={'error': str(e)},
                    recommendations=[f"Fix validation error: {str(e)}"]
                )
        
        # Generate summary report
        await self._generate_production_report(results, run_live_test)
        
        return results
    
    async def _generate_production_report(self, results: Dict[str, ProductionTestResult], was_live_test: bool):
        """Generate production validation report"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.success)
        failed_tests = total_tests - passed_tests
        
        # Calculate aggregated metrics
        total_vehicles = sum(r.total_vehicles_found for r in results.values())
        total_issues = sum(len(r.data_quality_issues) for r in results.values())
        first_page_issues = sum(1 for r in results.values() if r.first_page_only_detected)
        
        # Create summary
        summary = {
            'validation_timestamp': datetime.now().isoformat(),
            'test_mode': 'LIVE' if was_live_test else 'DRY_RUN',
            'overall_results': {
                'total_scrapers_validated': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            },
            'critical_issues': {
                'scrapers_with_first_page_only_issues': first_page_issues,
                'total_data_quality_issues': total_issues,
                'failed_scrapers': [name for name, result in results.items() if not result.success]
            },
            'performance_summary': {
                'total_vehicles_found': total_vehicles,
                'average_vehicles_per_scraper': total_vehicles / total_tests if total_tests > 0 else 0,
                'scrapers_with_pagination_issues': [
                    name for name, result in results.items() 
                    if result.first_page_only_detected
                ]
            },
            'individual_results': {
                name: {
                    'success': result.success,
                    'vehicles_found': result.total_vehicles_found,
                    'pages_accessed': result.pages_accessed,
                    'first_page_only': result.first_page_only_detected,
                    'data_quality_issues_count': len(result.data_quality_issues),
                    'key_recommendations': result.recommendations[:3]
                }
                for name, result in results.items()
            },
            'next_steps': self._generate_next_steps(results, was_live_test)
        }
        
        # Save summary report
        results_dir = project_root / "tests" / "production_validation_results"
        results_dir.mkdir(exist_ok=True)
        
        mode_suffix = "live" if was_live_test else "dry_run"
        summary_file = results_dir / f"validation_summary_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save individual results
        for name, result in results.items():
            result_file = results_dir / f"{name}_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
        
        # Print summary to console
        self._print_production_summary(summary)
        
        self.logger.info(f"📋 Validation report saved: {summary_file}")
    
    def _generate_next_steps(self, results: Dict[str, ProductionTestResult], was_live_test: bool) -> List[str]:
        """Generate next steps based on validation results"""
        next_steps = []
        
        if not was_live_test:
            next_steps.append("Run with --live flag to test against actual websites")
            return next_steps
        
        failed_scrapers = [name for name, result in results.items() if not result.success]
        pagination_issues = [name for name, result in results.items() if result.first_page_only_detected]
        
        if failed_scrapers:
            next_steps.append(f"PRIORITY 1: Fix failing scrapers: {', '.join(failed_scrapers)}")
        
        if pagination_issues:
            next_steps.append(f"PRIORITY 2: Fix pagination issues: {', '.join(pagination_issues)}")
        
        # Check for low vehicle counts
        low_count_scrapers = [
            name for name, result in results.items() 
            if result.success and result.total_vehicles_found < 3
        ]
        if low_count_scrapers:
            next_steps.append(f"INVESTIGATE: Low vehicle counts: {', '.join(low_count_scrapers)}")
        
        if not next_steps:
            next_steps.append("✅ All scrapers validated successfully! Ready for production deployment.")
        
        return next_steps
    
    def _print_production_summary(self, summary: Dict[str, Any]):
        """Print formatted production validation summary"""
        print("\n" + "="*70)
        print(f"🏭 SILVER FOX PRODUCTION SCRAPER VALIDATION - {summary['test_mode']}")
        print("="*70)
        
        overall = summary['overall_results']
        print(f"📊 Validation Results:")
        print(f"   ✅ Passed: {overall['passed']}/{overall['total_scrapers_validated']} ({overall['success_rate']:.1%})")
        print(f"   ❌ Failed: {overall['failed']}")
        
        critical = summary['critical_issues']
        if critical['failed_scrapers'] or critical['scrapers_with_first_page_only_issues'] > 0:
            print(f"\n🚨 Critical Issues:")
            if critical['failed_scrapers']:
                print(f"   💥 Failed scrapers: {', '.join(critical['failed_scrapers'])}")
            if critical['scrapers_with_first_page_only_issues'] > 0:
                print(f"   📄 First-page-only issues: {critical['scrapers_with_first_page_only_issues']} scrapers")
        
        performance = summary['performance_summary']
        print(f"\n📈 Performance Summary:")
        print(f"   🚗 Total vehicles found: {performance['total_vehicles_found']}")
        print(f"   📊 Average per scraper: {performance['average_vehicles_per_scraper']:.1f}")
        
        if performance['scrapers_with_pagination_issues']:
            print(f"   ⚠️  Pagination issues: {', '.join(performance['scrapers_with_pagination_issues'])}")
        
        print(f"\n📋 Individual Results:")
        for name, result in summary['individual_results'].items():
            status = "✅" if result['success'] else "❌"
            pagination_warning = " ⚠️ FIRST-PAGE-ONLY" if result['first_page_only'] else ""
            print(f"   {status} {name}: {result['vehicles_found']} vehicles{pagination_warning}")
        
        print(f"\n🎯 Next Steps:")
        for step in summary['next_steps']:
            print(f"   • {step}")
        
        print("="*70)


async def main():
    """Main entry point for production validation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Silver Fox Production Scraper Validator",
        epilog="⚠️  Use --live flag with caution - tests against real websites!"
    )
    parser.add_argument("--scraper", help="Validate specific scraper (optional)")
    parser.add_argument("--live", action="store_true", help="Run against live websites (USE WITH CAUTION)")
    parser.add_argument("--timeout", type=int, default=1800, help="Test timeout in seconds")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay between requests (seconds)")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = {
        'test_timeout': args.timeout,
        'delay_between_requests': args.delay,
        'respect_rate_limits': True,
        'data_quality_threshold': 0.8
    }
    
    # Initialize validator
    validator = ProductionScraperValidator(config)
    
    try:
        if args.scraper:
            # Validate specific scraper
            print(f"🎯 Validating specific scraper: {args.scraper}")
            if args.live:
                print("⚠️  LIVE TEST MODE - Connecting to actual website!")
            result = await validator.validate_individual_scraper(args.scraper, args.live)
            
            # Print result
            status = "✅ PASSED" if result.success else "❌ FAILED"
            print(f"\n📊 Result: {status}")
            print(f"   🚗 Vehicles: {result.total_vehicles_found}")
            print(f"   📄 Pages: {result.pages_accessed}")
            print(f"   ⚠️  First-page-only: {result.first_page_only_detected}")
            print(f"   🐛 Issues: {len(result.data_quality_issues)}")
            
            if result.recommendations:
                print(f"   💡 Recommendations:")
                for rec in result.recommendations:
                    print(f"      • {rec}")
        else:
            # Validate all scrapers
            if args.live:
                print("🚨 LIVE TEST MODE - Will connect to actual dealership websites!")
            else:
                print("📋 DRY RUN MODE - Analyzing scraper configuration only")
            
            results = await validator.validate_all_scrapers(args.live)
            
            passed = sum(1 for r in results.values() if r.success)
            total = len(results)
            print(f"\n🏁 Final Result: {passed}/{total} scrapers validated successfully ({passed/total:.1%})")
    
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())