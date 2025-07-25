#!/usr/bin/env python3
"""
Comprehensive Scraper Testing System
===================================

Test all 40 scrapers individually to ensure they're fully functional
and actually scraping data. Provides detailed validation reports.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import time
import logging
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import traceback

class ComprehensiveScraperTester:
    """Test all scrapers comprehensively"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.scrapers_dir = self.project_root / "silverfox_system" / "core" / "scrapers" / "dealerships"
        self.logger = logging.getLogger(__name__)
        
        # Add scrapers directory to Python path
        sys.path.insert(0, str(self.scrapers_dir))
        
        # Test results tracking
        self.test_results = {
            'total_scrapers': 0,
            'successful_scrapers': 0,
            'failed_scrapers': 0,
            'scrapers_with_data': 0,
            'scrapers_with_fallback': 0,
            'scrapers_with_errors': 0,
            'total_vehicles_found': 0,
            'individual_results': [],
            'test_start': datetime.now().isoformat(),
            'test_duration': 0
        }
    
    def test_all_scrapers(self) -> Dict[str, Any]:
        """Test all scrapers comprehensively"""
        self.logger.info("🚀 Starting comprehensive scraper testing")
        test_start_time = time.time()
        
        # Get all optimized scrapers
        scraper_files = list(self.scrapers_dir.glob("*_optimized.py"))
        self.test_results['total_scrapers'] = len(scraper_files)
        
        self.logger.info(f"📊 Found {len(scraper_files)} optimized scrapers to test")
        
        # Test each scraper individually
        for i, scraper_file in enumerate(scraper_files):
            try:
                self.logger.info(f"🔍 Testing scraper {i+1}/{len(scraper_files)}: {scraper_file.stem}")
                
                result = self._test_individual_scraper(scraper_file)
                self.test_results['individual_results'].append(result)
                
                # Update counters
                if result['success']:
                    self.test_results['successful_scrapers'] += 1
                    if result['vehicle_count'] > 0:
                        self.test_results['scrapers_with_data'] += 1
                        self.test_results['total_vehicles_found'] += result['vehicle_count']
                    if result['data_source'] == 'fallback':
                        self.test_results['scrapers_with_fallback'] += 1
                else:
                    self.test_results['failed_scrapers'] += 1
                    self.test_results['scrapers_with_errors'] += 1
                
                # Print progress
                self._print_progress(i + 1, len(scraper_files), result)
                
            except Exception as e:
                self.logger.error(f"❌ Critical error testing {scraper_file.stem}: {e}")
                error_result = {
                    'scraper_name': scraper_file.stem,
                    'dealer_name': self._extract_dealer_name(scraper_file.stem),
                    'success': False,
                    'error': f"Critical test error: {str(e)}",
                    'vehicle_count': 0,
                    'data_source': 'error'
                }
                self.test_results['individual_results'].append(error_result)
                self.test_results['failed_scrapers'] += 1
                self.test_results['scrapers_with_errors'] += 1
        
        # Calculate final metrics
        self.test_results['test_duration'] = time.time() - test_start_time
        self.test_results['success_rate'] = (
            self.test_results['successful_scrapers'] / self.test_results['total_scrapers'] * 100
            if self.test_results['total_scrapers'] > 0 else 0
        )
        self.test_results['data_rate'] = (
            self.test_results['scrapers_with_data'] / self.test_results['total_scrapers'] * 100
            if self.test_results['total_scrapers'] > 0 else 0
        )
        
        # Save comprehensive report
        self._save_test_report()
        
        # Print final summary
        self._print_final_summary()
        
        return self.test_results
    
    def _test_individual_scraper(self, scraper_file: Path) -> Dict[str, Any]:
        """Test an individual scraper"""
        scraper_name = scraper_file.stem
        dealer_name = self._extract_dealer_name(scraper_name)
        
        result = {
            'scraper_name': scraper_name,
            'dealer_name': dealer_name,
            'success': False,
            'vehicle_count': 0,
            'data_source': 'unknown',
            'test_duration': 0,
            'error': None,
            'sample_vehicle': None,
            'data_quality': {},
            'test_timestamp': datetime.now().isoformat()
        }
        
        test_start = time.time()
        
        try:
            # Import the scraper module
            module_name = scraper_name
            module = importlib.import_module(module_name)
            
            # Find the scraper class
            class_name = self._get_expected_class_name(dealer_name)
            if not hasattr(module, class_name):
                # Try alternative class name patterns
                possible_names = [
                    class_name,
                    f"{dealer_name.replace(' ', '').replace('-', '')}OptimizedScraper",
                    f"{scraper_name.replace('_optimized', '').title()}Scraper"
                ]
                
                scraper_class = None
                for name in possible_names:
                    if hasattr(module, name):
                        scraper_class = getattr(module, name)
                        break
                
                if not scraper_class:
                    result['error'] = f"Could not find scraper class. Tried: {possible_names}"
                    return result
            else:
                scraper_class = getattr(module, class_name)
            
            # Instantiate and test the scraper
            scraper = scraper_class()
            
            # Call the main scraping method
            vehicles = scraper.get_all_vehicles()
            
            # Analyze results
            if vehicles and len(vehicles) > 0:
                result['success'] = True
                result['vehicle_count'] = len(vehicles)
                
                # Determine data source
                first_vehicle = vehicles[0]
                if isinstance(first_vehicle, dict):
                    result['data_source'] = first_vehicle.get('data_source', 'unknown')
                    result['sample_vehicle'] = {
                        'vin': first_vehicle.get('vin', 'N/A'),
                        'year': first_vehicle.get('year', 'N/A'),
                        'make': first_vehicle.get('make', 'N/A'),
                        'model': first_vehicle.get('model', 'N/A'),
                        'price': first_vehicle.get('price', 'N/A')
                    }
                    
                    # Analyze data quality
                    result['data_quality'] = self._analyze_data_quality(vehicles)
                else:
                    result['data_source'] = 'error_format'
                    result['error'] = "Invalid vehicle data format"
                    result['success'] = False
            else:
                result['success'] = False
                result['error'] = "No vehicles returned"
                result['vehicle_count'] = 0
        
        except ImportError as e:
            result['error'] = f"Import error: {str(e)}"
        except AttributeError as e:
            result['error'] = f"Class/method not found: {str(e)}"
        except Exception as e:
            result['error'] = f"Runtime error: {str(e)}"
            result['traceback'] = traceback.format_exc()
        
        finally:
            result['test_duration'] = time.time() - test_start
        
        return result
    
    def _analyze_data_quality(self, vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data quality of scraped vehicles"""
        if not vehicles:
            return {'score': 0.0, 'issues': ['No vehicles']}
        
        quality_metrics = {
            'total_vehicles': len(vehicles),
            'complete_records': 0,
            'price_range': {'min': None, 'max': None, 'avg': None},
            'year_range': {'min': None, 'max': None},
            'unique_vins': 0,
            'data_completeness': 0.0,
            'score': 0.0,
            'issues': []
        }
        
        # Analyze each vehicle
        prices = []
        years = []
        vins = set()
        complete_records = 0
        
        required_fields = ['vin', 'year', 'make', 'model']
        
        for vehicle in vehicles:
            if not isinstance(vehicle, dict):
                continue
            
            # Check completeness
            if all(vehicle.get(field) for field in required_fields):
                complete_records += 1
            
            # Collect price data
            if vehicle.get('price') and isinstance(vehicle['price'], (int, float)):
                prices.append(vehicle['price'])
            
            # Collect year data
            if vehicle.get('year') and isinstance(vehicle['year'], int):
                years.append(vehicle['year'])
            
            # Collect VIN data
            if vehicle.get('vin'):
                vins.add(vehicle['vin'])
        
        # Calculate metrics
        quality_metrics['complete_records'] = complete_records
        quality_metrics['data_completeness'] = complete_records / len(vehicles)
        quality_metrics['unique_vins'] = len(vins)
        
        if prices:
            quality_metrics['price_range'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices)
            }
        
        if years:
            quality_metrics['year_range'] = {
                'min': min(years),
                'max': max(years)
            }
        
        # Identify issues
        if len(vins) < len(vehicles):
            quality_metrics['issues'].append(f"Duplicate VINs: {len(vehicles) - len(vins)} duplicates")
        
        if quality_metrics['data_completeness'] < 0.8:
            quality_metrics['issues'].append(f"Low completeness: {quality_metrics['data_completeness']:.1%}")
        
        if not prices:
            quality_metrics['issues'].append("No price data available")
        
        # Calculate overall score
        completeness_score = quality_metrics['data_completeness']
        uniqueness_score = len(vins) / len(vehicles) if vehicles else 0
        data_presence_score = 1.0 if prices and years else 0.5
        
        quality_metrics['score'] = (completeness_score * 0.4 + uniqueness_score * 0.3 + data_presence_score * 0.3)
        
        return quality_metrics
    
    def _extract_dealer_name(self, scraper_name: str) -> str:
        """Extract dealer name from scraper filename"""
        base_name = scraper_name.replace('_optimized', '').replace('_working', '')
        
        # Special mappings for known dealers
        name_mappings = {
            'bmwofweststlouis': 'BMW of West St. Louis',
            'columbiabmw': 'Columbia BMW',
            'jaguarranchomirage': 'Jaguar Ranch Mirage',
            'landroverranchomirage': 'Land Rover Ranch Mirage',
            'suntrupfordwest': 'Suntrup Ford West',
            'joemachenshyundai': 'Joe Machens Hyundai',
            'columbiahonda': 'Columbia Honda',
            'audiranchomirage': 'Audi Ranch Mirage',
            'auffenberghyundai': 'Auffenberg Hyundai',
            'bommaritocadillac': 'Bommarito Cadillac',
            'bommaritowestcounty': 'Bommarito West County',
            'davesinclairlincolnsouth': 'Dave Sinclair Lincoln South',
            'davesinclairlincolnstpeters': 'Dave Sinclair Lincoln St. Peters',
            'frankletahonda': 'Frank Leta Honda',
            'glendalechryslerjeep': 'Glendale Chrysler Jeep',
            'hondafrontenac': 'Honda of Frontenac',
            'hwkia': 'H&W Kia',
            'indigoautogroup': 'Indigo Auto Group',
            'joemachenscdjr': 'Joe Machens Chrysler Dodge Jeep Ram',
            'joemachensnissan': 'Joe Machens Nissan',
            'joemachenstoyota': 'Joe Machens Toyota',
            'kiaofcolumbia': 'Kia of Columbia',
            'miniofstlouis': 'MINI of St. Louis',
            'pappastoyota': 'Pappas Toyota',
            'porschestlouis': 'Porsche St. Louis',
            'pundmannford': 'Pundmann Ford',
            'rustydrewingcadillac': 'Rusty Drewing Cadillac',
            'rustydrewingchevroletbuickgmc': 'Rusty Drewing Chevrolet Buick GMC',
            'serrahondaofallon': 'Serra Honda of O\'Fallon',
            'southcountyautos': 'South County Autos',
            'spiritlexus': 'Spirit Lexus',
            'stehouwerauto': 'Stehouwer Auto',
            'suntrupbuickgmc': 'Suntrup Buick GMC',
            'suntrupfordkirkwood': 'Suntrup Ford Kirkwood',
            'suntruphyundaisouth': 'Suntrup Hyundai South',
            'suntrupkiasouth': 'Suntrup Kia South',
            'thoroughbredford': 'Thoroughbred Ford',
            'twincitytoyota': 'Twin City Toyota',
            'wcvolvocars': 'West County Volvo Cars',
            'weberchev': 'Weber Chevrolet'
        }
        
        return name_mappings.get(base_name, base_name.replace('_', ' ').title())
    
    def _get_expected_class_name(self, dealer_name: str) -> str:
        """Get expected class name for dealer"""
        # Convert dealer name to PascalCase
        clean_name = ''.join(char for char in dealer_name if char.isalnum() or char.isspace())
        words = clean_name.split()
        class_name = ''.join(word.capitalize() for word in words)
        return f"{class_name}OptimizedScraper"
    
    def _print_progress(self, current: int, total: int, result: Dict[str, Any]) -> None:
        """Print test progress"""
        status = "✅" if result['success'] else "❌"
        vehicle_count = result['vehicle_count']
        data_source = result['data_source']
        
        print(f"{status} {current:2d}/{total} | {result['dealer_name']:<35} | {vehicle_count:3d} vehicles | {data_source}")
    
    def _print_final_summary(self) -> None:
        """Print comprehensive final summary"""
        print("\n" + "="*80)
        print("🏁 COMPREHENSIVE SCRAPER TESTING COMPLETE")
        print("="*80)
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Scrapers Tested: {self.test_results['total_scrapers']}")
        print(f"   ✅ Successful: {self.test_results['successful_scrapers']} ({self.test_results['success_rate']:.1f}%)")
        print(f"   ❌ Failed: {self.test_results['failed_scrapers']}")
        print(f"   🚗 Total Vehicles Found: {self.test_results['total_vehicles_found']}")
        print(f"   📊 Scrapers with Data: {self.test_results['scrapers_with_data']} ({self.test_results['data_rate']:.1f}%)")
        print(f"   🔄 Using Fallback Data: {self.test_results['scrapers_with_fallback']}")
        print(f"   ⏱️  Test Duration: {self.test_results['test_duration']:.2f}s")
        
        # Breakdown by data source
        data_sources = {}
        for result in self.test_results['individual_results']:
            source = result['data_source']
            data_sources[source] = data_sources.get(source, 0) + 1
        
        print(f"\n📈 DATA SOURCE BREAKDOWN:")
        for source, count in sorted(data_sources.items()):
            percentage = count / self.test_results['total_scrapers'] * 100
            print(f"   {source:<20}: {count:2d} scrapers ({percentage:4.1f}%)")
        
        # Top performers
        successful_results = [r for r in self.test_results['individual_results'] if r['success']]
        if successful_results:
            top_performers = sorted(successful_results, key=lambda x: x['vehicle_count'], reverse=True)[:5]
            print(f"\n🏆 TOP PERFORMERS:")
            for i, result in enumerate(top_performers):
                print(f"   {i+1}. {result['dealer_name']:<35} | {result['vehicle_count']} vehicles")
        
        # Failed scrapers
        failed_results = [r for r in self.test_results['individual_results'] if not r['success']]
        if failed_results:
            print(f"\n⚠️  FAILED SCRAPERS ({len(failed_results)}):")
            for result in failed_results:
                print(f"   ❌ {result['dealer_name']:<35} | {result['error']}")
    
    def _save_test_report(self) -> None:
        """Save comprehensive test report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.project_root / f"comprehensive_test_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            self.logger.info(f"📋 Test report saved: {report_file}")
            print(f"\n📋 Detailed report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Could not save test report: {e}")

def main():
    """Main execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 COMPREHENSIVE SCRAPER TESTING")
    print("="*50)
    print("Testing all 40 scrapers individually...")
    print("Status | #  | Dealer Name                         | Vehicles | Data Source")
    print("-"*80)
    
    tester = ComprehensiveScraperTester()
    results = tester.test_all_scrapers()
    
    return results

if __name__ == "__main__":
    main()