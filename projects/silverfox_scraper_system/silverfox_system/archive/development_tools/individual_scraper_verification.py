#!/usr/bin/env python3
"""
Individual Scraper Verification System
Tests each scraper one-by-one to ensure complete inventory coverage
Critical for accurate new/pre-owned/CPO normalization
"""

import os
import sys
import json
import time
import importlib
import importlib.util
import requests
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

class IndividualScraperVerifier:
    """Verify each scraper individually for complete inventory coverage"""
    
    def __init__(self):
        self.scrapers_dir = Path(__file__).parent / 'scraper' / 'dealerships'
        self.verification_results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def verify_all_scrapers(self, limit: int = None) -> Dict:
        """Verify all scrapers individually"""
        print("🔍 INDIVIDUAL SCRAPER VERIFICATION")
        print("=" * 60)
        print("Testing each scraper for complete inventory coverage")
        print("Critical for accurate new/pre-owned/CPO normalization")
        print()
        
        working_scrapers = list(self.scrapers_dir.glob("*_working.py"))
        if limit:
            working_scrapers = working_scrapers[:limit]
        
        print(f"📊 Testing {len(working_scrapers)} scrapers individually")
        print()
        
        for i, scraper_file in enumerate(working_scrapers, 1):
            dealership_id = scraper_file.stem.replace('_working', '')
            
            print(f"🔍 [{i}/{len(working_scrapers)}] Verifying: {dealership_id}")
            print("-" * 50)
            
            verification_result = self._verify_single_scraper(dealership_id, scraper_file)
            self.verification_results[dealership_id] = verification_result
            
            # Print immediate results
            self._print_verification_result(dealership_id, verification_result)
            print()
            
            # Rate limiting between tests
            time.sleep(2)
        
        # Generate comprehensive report
        self._generate_verification_report()
        return self.verification_results
    
    def _verify_single_scraper(self, dealership_id: str, scraper_file: Path) -> Dict:
        """Verify a single scraper for complete inventory coverage"""
        
        verification = {
            'dealership_id': dealership_id,
            'status': 'UNKNOWN',
            'website_inventory_count': 0,
            'scraper_inventory_count': 0,
            'coverage_percentage': 0.0,
            'issues': [],
            'recommendations': [],
            'api_type': 'unknown',
            'test_timestamp': datetime.now().isoformat(),
            'website_accessible': False,
            'scraper_functional': False,
            'pagination_working': False,
            'sample_vehicles': []
        }
        
        try:
            # Step 1: Check website accessibility
            verification.update(self._check_website_accessibility(dealership_id))
            
            # Step 2: Get expected inventory count from website
            if verification['website_accessible']:
                verification.update(self._get_website_inventory_count(dealership_id))
            
            # Step 3: Test scraper functionality
            verification.update(self._test_scraper_functionality(dealership_id, scraper_file))
            
            # Step 4: Compare results and calculate coverage
            verification = self._calculate_coverage_metrics(verification)
            
        except Exception as e:
            verification['status'] = 'ERROR'
            verification['issues'].append(f'Verification failed: {str(e)}')
            self.logger.error(f"Error verifying {dealership_id}: {str(e)}")
        
        return verification
    
    def _check_website_accessibility(self, dealership_id: str) -> Dict:
        """Check if the dealership website is accessible"""
        result = {
            'website_accessible': False,
            'website_url': '',
            'response_time': 0.0
        }
        
        # Get website URL from configuration
        try:
            from configure_all_dealerships import DEALERSHIP_CONFIGURATIONS
            config = DEALERSHIP_CONFIGURATIONS.get(dealership_id, {})
            website_url = config.get('base_url', '')
            
            if not website_url:
                result['issues'] = ['No website URL found in configuration']
                return result
            
            result['website_url'] = website_url
            
            # Test website accessibility
            start_time = time.time()
            response = self.session.get(website_url, timeout=10)
            result['response_time'] = time.time() - start_time
            
            if response.status_code == 200:
                result['website_accessible'] = True
                print(f"   ✅ Website accessible: {website_url} ({result['response_time']:.2f}s)")
            else:
                result['issues'] = [f'Website returned status {response.status_code}']
                print(f"   ❌ Website issue: Status {response.status_code}")
                
        except Exception as e:
            result['issues'] = [f'Website accessibility error: {str(e)}']
            print(f"   ❌ Website error: {str(e)}")
        
        return result
    
    def _get_website_inventory_count(self, dealership_id: str) -> Dict:
        """Get expected inventory count from the website"""
        result = {
            'website_inventory_count': 0,
            'inventory_detection_method': 'none'
        }
        
        try:
            from configure_all_dealerships import DEALERSHIP_CONFIGURATIONS
            config = DEALERSHIP_CONFIGURATIONS.get(dealership_id, {})
            api_platform = config.get('api_platform', 'unknown')
            website_url = config.get('base_url', '')
            
            result['api_type'] = api_platform
            
            if api_platform == 'algolia':
                result.update(self._check_algolia_inventory_count(config))
            elif api_platform == 'dealeron_cosmos':
                result.update(self._check_dealeron_inventory_count(config))
            elif api_platform == 'stellantis_ddc':
                result.update(self._check_ddc_inventory_count(config))
            else:
                result.update(self._check_generic_inventory_count(website_url))
                
        except Exception as e:
            result['issues'] = result.get('issues', []) + [f'Inventory count error: {str(e)}']
        
        return result
    
    def _check_algolia_inventory_count(self, config: Dict) -> Dict:
        """Check inventory count for Algolia-based dealerships"""
        result = {
            'website_inventory_count': 0,
            'inventory_detection_method': 'algolia_api'
        }
        
        try:
            # Extract Algolia configuration
            api_config = config.get('api_config', {})
            algolia_app_id = api_config.get('algolia_app_id', '')
            algolia_api_key = api_config.get('algolia_api_key', '')
            
            if not algolia_app_id or not algolia_api_key:
                # Try to find Algolia config from website
                website_url = config.get('base_url', '')
                inventory_page = f"{website_url}/inventory"
                
                response = self.session.get(inventory_page, timeout=10)
                content = response.text
                
                # Look for Algolia configuration in page source
                import re
                app_id_match = re.search(r'applicationId["\']:\s*["\']([^"\']+)', content)
                api_key_match = re.search(r'apiKey["\']:\s*["\']([^"\']+)', content)
                
                if app_id_match and api_key_match:
                    algolia_app_id = app_id_match.group(1)
                    algolia_api_key = api_key_match.group(1)
                    print(f"   🔍 Found Algolia config: {algolia_app_id}")
            
            if algolia_app_id and algolia_api_key:
                # Make test Algolia query to get total count
                algolia_url = f"https://{algolia_app_id}-dsn.algolia.net/1/indexes/*/queries"
                
                query_data = {
                    "requests": [{
                        "indexName": "vehicles_production",  # Common index name
                        "params": "query=&hitsPerPage=0&page=0"  # Get count only
                    }]
                }
                
                headers = {
                    'X-Algolia-Application-Id': algolia_app_id,
                    'X-Algolia-API-Key': algolia_api_key,
                    'Content-Type': 'application/json'
                }
                
                response = self.session.post(algolia_url, json=query_data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        total_hits = data['results'][0].get('nbHits', 0)
                        result['website_inventory_count'] = total_hits
                        print(f"   📊 Algolia inventory count: {total_hits} vehicles")
                    else:
                        result['issues'] = ['Algolia API returned no results']
                else:
                    result['issues'] = [f'Algolia API error: {response.status_code}']
            else:
                result['issues'] = ['Could not find Algolia configuration']
                
        except Exception as e:
            result['issues'] = [f'Algolia check error: {str(e)}']
        
        return result
    
    def _check_dealeron_inventory_count(self, config: Dict) -> Dict:
        """Check inventory count for DealerOn-based dealerships"""
        result = {
            'website_inventory_count': 0,
            'inventory_detection_method': 'dealeron_api'
        }
        
        try:
            website_url = config.get('base_url', '')
            inventory_api = f"{website_url}/inventory-feed"
            
            response = self.session.get(inventory_api, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get('total', 0)
                result['website_inventory_count'] = total_count
                print(f"   📊 DealerOn inventory count: {total_count} vehicles")
            else:
                # Fallback: check inventory page
                result.update(self._check_generic_inventory_count(website_url))
                
        except Exception as e:
            result['issues'] = [f'DealerOn check error: {str(e)}']
            # Fallback to generic check
            result.update(self._check_generic_inventory_count(config.get('base_url', '')))
        
        return result
    
    def _check_ddc_inventory_count(self, config: Dict) -> Dict:
        """Check inventory count for DDC-based dealerships"""
        result = {
            'website_inventory_count': 0,
            'inventory_detection_method': 'ddc_api'
        }
        
        try:
            website_url = config.get('base_url', '')
            
            # Try DDC API endpoint
            api_config = config.get('api_config', {})
            api_endpoint = api_config.get('primary_endpoint', f"{website_url}/inventory/feed/vehicles")
            
            response = self.session.get(api_endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                vehicles = data.get('vehicles', [])
                total_count = len(vehicles)
                result['website_inventory_count'] = total_count
                print(f"   📊 DDC inventory count: {total_count} vehicles")
            else:
                result.update(self._check_generic_inventory_count(website_url))
                
        except Exception as e:
            result['issues'] = [f'DDC check error: {str(e)}']
            result.update(self._check_generic_inventory_count(config.get('base_url', '')))
        
        return result
    
    def _check_generic_inventory_count(self, website_url: str) -> Dict:
        """Generic inventory count check for any website"""
        result = {
            'website_inventory_count': 0,
            'inventory_detection_method': 'page_scraping'
        }
        
        try:
            inventory_page = f"{website_url}/inventory"
            response = self.session.get(inventory_page, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for common inventory count indicators
                import re
                
                # Common patterns for inventory counts
                patterns = [
                    r'(\d+)\s+(?:vehicles?|cars?|results?)',
                    r'(?:showing|found|total):\s*(\d+)',
                    r'(\d+)\s+(?:of|total)',
                    r'inventory-count["\']>\s*(\d+)',
                    r'total["\']:\s*(\d+)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Get the highest number found (likely the total)
                        counts = [int(m) for m in matches if int(m) > 10]  # Filter out small numbers
                        if counts:
                            result['website_inventory_count'] = max(counts)
                            print(f"   📊 Estimated inventory count: {max(counts)} vehicles")
                            break
                
                if result['website_inventory_count'] == 0:
                    # Count vehicle elements on the page as a fallback
                    vehicle_patterns = [
                        r'class=["\'][^"\']*vehicle[^"\']*["\']',
                        r'class=["\'][^"\']*car[^"\']*["\']',
                        r'class=["\'][^"\']*listing[^"\']*["\']'
                    ]
                    
                    for pattern in vehicle_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if len(matches) > 5:  # Must have several vehicles
                            result['website_inventory_count'] = len(matches) * 10  # Estimate total from page
                            result['inventory_detection_method'] = 'element_counting'
                            print(f"   📊 Estimated from page elements: ~{result['website_inventory_count']} vehicles")
                            break
            
        except Exception as e:
            result['issues'] = [f'Generic check error: {str(e)}']
        
        return result
    
    def _test_scraper_functionality(self, dealership_id: str, scraper_file: Path) -> Dict:
        """Test the actual scraper functionality"""
        result = {
            'scraper_functional': False,
            'scraper_inventory_count': 0,
            'pagination_working': False,
            'sample_vehicles': [],
            'scraper_errors': []
        }
        
        try:
            print(f"   🧪 Testing scraper functionality...")
            
            # Import and instantiate the scraper
            spec = importlib.util.spec_from_file_location(dealership_id, scraper_file)
            scraper_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(scraper_module)
            
            # Find the scraper class
            scraper_class = None
            for attr_name in dir(scraper_module):
                attr = getattr(scraper_module, attr_name)
                if isinstance(attr, type) and 'scraper' in attr_name.lower():
                    scraper_class = attr
                    break
            
            if scraper_class:
                # Create scraper instance
                scraper = scraper_class()
                
                # Test scraping with a small limit first
                if hasattr(scraper, 'scrape_inventory'):
                    vehicles = scraper.scrape_inventory(max_vehicles=50)  # Test with limit
                    
                    if vehicles:
                        result['scraper_functional'] = True
                        result['scraper_inventory_count'] = len(vehicles)
                        result['sample_vehicles'] = vehicles[:3]  # First 3 as samples
                        
                        print(f"   ✅ Scraper functional: {len(vehicles)} vehicles found")
                        
                        # Test pagination by checking for more vehicles
                        if hasattr(scraper, '_scrape_with_complete_pagination'):
                            full_vehicles = scraper._scrape_with_complete_pagination()
                            if len(full_vehicles) > len(vehicles):
                                result['pagination_working'] = True
                                result['scraper_inventory_count'] = len(full_vehicles)
                                print(f"   ✅ Pagination working: {len(full_vehicles)} total vehicles")
                        
                    else:
                        result['scraper_errors'].append('Scraper returned no vehicles')
                        print(f"   ❌ Scraper returned no vehicles")
                else:
                    result['scraper_errors'].append('No scrape_inventory method found')
            else:
                result['scraper_errors'].append('No scraper class found in module')
                
        except Exception as e:
            result['scraper_errors'].append(f'Scraper test error: {str(e)}')
            print(f"   ❌ Scraper error: {str(e)}")
        
        return result
    
    def _calculate_coverage_metrics(self, verification: Dict) -> Dict:
        """Calculate coverage metrics and final status"""
        
        website_count = verification.get('website_inventory_count', 0)
        scraper_count = verification.get('scraper_inventory_count', 0)
        
        if website_count > 0 and scraper_count > 0:
            coverage = (scraper_count / website_count) * 100
            verification['coverage_percentage'] = round(coverage, 1)
            
            if coverage >= 90:
                verification['status'] = 'EXCELLENT'
            elif coverage >= 75:
                verification['status'] = 'GOOD'
            elif coverage >= 50:
                verification['status'] = 'PARTIAL'
            else:
                verification['status'] = 'POOR'
                
        elif scraper_count > 0 and website_count == 0:
            verification['status'] = 'SCRAPER_WORKING'
            verification['coverage_percentage'] = 100.0  # Can't compare, but scraper works
            
        elif website_count > 0 and scraper_count == 0:
            verification['status'] = 'SCRAPER_BROKEN'
            verification['coverage_percentage'] = 0.0
            
        else:
            verification['status'] = 'UNKNOWN'
            verification['coverage_percentage'] = 0.0
        
        # Generate recommendations
        recommendations = []
        
        if verification['coverage_percentage'] < 90:
            recommendations.append('Improve pagination to capture more vehicles')
        
        if not verification.get('pagination_working', False):
            recommendations.append('Implement complete pagination system')
        
        if verification.get('website_inventory_count', 0) == 0:
            recommendations.append('Verify website inventory detection method')
        
        if not verification.get('scraper_functional', False):
            recommendations.append('Fix scraper functionality issues')
        
        verification['recommendations'] = recommendations
        
        return verification
    
    def _print_verification_result(self, dealership_id: str, result: Dict):
        """Print individual verification result"""
        status_icons = {
            'EXCELLENT': '✅',
            'GOOD': '✅', 
            'PARTIAL': '⚠️',
            'POOR': '❌',
            'SCRAPER_WORKING': '⚠️',
            'SCRAPER_BROKEN': '❌',
            'UNKNOWN': '❓',
            'ERROR': '💥'
        }
        
        status = result.get('status', 'UNKNOWN')
        icon = status_icons.get(status, '❓')
        
        print(f"   {icon} Status: {status}")
        print(f"   📊 Website: {result.get('website_inventory_count', 0)} vehicles")
        print(f"   🤖 Scraper: {result.get('scraper_inventory_count', 0)} vehicles")
        print(f"   📈 Coverage: {result.get('coverage_percentage', 0)}%")
        
        if result.get('issues'):
            print(f"   ⚠️  Issues: {'; '.join(result['issues'][:2])}")
        
        if result.get('recommendations'):
            print(f"   💡 Recommendations: {'; '.join(result['recommendations'][:2])}")
    
    def _generate_verification_report(self):
        """Generate comprehensive verification report"""
        print("\n" + "=" * 70)
        print("📋 INDIVIDUAL SCRAPER VERIFICATION REPORT")
        print("=" * 70)
        
        total = len(self.verification_results)
        excellent = sum(1 for r in self.verification_results.values() if r.get('status') == 'EXCELLENT')
        good = sum(1 for r in self.verification_results.values() if r.get('status') == 'GOOD')
        partial = sum(1 for r in self.verification_results.values() if r.get('status') == 'PARTIAL')
        poor = sum(1 for r in self.verification_results.values() if r.get('status') in ['POOR', 'SCRAPER_BROKEN'])
        
        print(f"📊 SUMMARY:")
        print(f"   Total Scrapers Tested: {total}")
        print(f"   ✅ Excellent Coverage (90%+): {excellent} ({excellent/total*100:.1f}%)")
        print(f"   ✅ Good Coverage (75-89%): {good} ({good/total*100:.1f}%)")
        print(f"   ⚠️ Partial Coverage (50-74%): {partial} ({partial/total*100:.1f}%)")
        print(f"   ❌ Poor/Broken (<50%): {poor} ({poor/total*100:.1f}%)")
        print()
        
        # Save detailed report
        report_file = f"scraper_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.verification_results, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file}")
        print()
        
        # Show critical issues
        critical_issues = [
            (dealership_id, result) for dealership_id, result in self.verification_results.items()
            if result.get('status') in ['POOR', 'SCRAPER_BROKEN', 'ERROR']
        ]
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for dealership_id, result in critical_issues[:10]:
                coverage = result.get('coverage_percentage', 0)
                print(f"   ❌ {dealership_id}: {result.get('status')} ({coverage}% coverage)")
                if result.get('recommendations'):
                    print(f"      💡 {result['recommendations'][0]}")
            print()

def main():
    """Run individual scraper verification"""
    verifier = IndividualScraperVerifier()
    
    print("🎯 Silver Fox Marketing - Individual Scraper Verification")
    print("Testing each scraper for complete inventory coverage")
    print("Critical for accurate new/pre-owned/CPO normalization")
    print()
    
    # Start with first 3 scrapers for testing
    limit = 3
    print(f"Testing first {limit} scrapers to verify system...")
    
    verifier.verify_all_scrapers(limit=limit)

if __name__ == "__main__":
    main()