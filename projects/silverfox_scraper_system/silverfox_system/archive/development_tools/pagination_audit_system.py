#!/usr/bin/env python3
"""
Pagination Audit System - Ensures Complete Inventory Coverage
Critical for accurate normalization of new/pre-owned/CPO vehicles
"""

import os
import sys
import json
import re
import ast
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

class PaginationAuditor:
    """Comprehensive pagination audit and enforcement system"""
    
    def __init__(self):
        self.scrapers_dir = Path(__file__).parent / 'scraper' / 'dealerships'
        self.audit_results = {}
        self.critical_issues = []
        self.recommendations = []
        
    def audit_all_scrapers(self) -> Dict:
        """Audit pagination implementation across all working scrapers"""
        print("🔍 PAGINATION AUDIT - Ensuring Complete Inventory Coverage")
        print("=" * 70)
        
        working_scrapers = list(self.scrapers_dir.glob("*_working.py"))
        print(f"📊 Found {len(working_scrapers)} working scrapers to audit")
        print()
        
        for scraper_file in working_scrapers:
            dealership_id = scraper_file.stem.replace('_working', '')
            print(f"🔍 Auditing: {dealership_id}")
            
            audit_result = self._audit_single_scraper(scraper_file)
            self.audit_results[dealership_id] = audit_result
            
            # Print status
            status = "✅" if audit_result['pagination_score'] >= 8 else "⚠️" if audit_result['pagination_score'] >= 6 else "❌"
            print(f"   {status} Score: {audit_result['pagination_score']}/10 - {audit_result['status']}")
            
            if audit_result['pagination_score'] < 8:
                self.critical_issues.append({
                    'dealership': dealership_id,
                    'score': audit_result['pagination_score'],
                    'issues': audit_result['issues']
                })
        
        print()
        self._generate_audit_report()
        return self.audit_results
    
    def _audit_single_scraper(self, scraper_file: Path) -> Dict:
        """Audit a single scraper for pagination completeness"""
        try:
            with open(scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'status': 'ERROR',
                'pagination_score': 0,
                'issues': [f'Failed to read file: {str(e)}'],
                'recommendations': ['Fix file access issues'],
                'has_pagination': False,
                'has_completion_check': False,
                'has_inventory_verification': False
            }
        
        # Initialize audit metrics
        audit = {
            'status': 'UNKNOWN',
            'pagination_score': 0,
            'issues': [],
            'recommendations': [],
            'has_pagination': False,
            'has_completion_check': False,
            'has_inventory_verification': False,
            'pagination_patterns': [],
            'completion_patterns': [],
            'api_type': 'unknown'
        }
        
        # 1. Check for pagination loop patterns (2 points)
        pagination_patterns = [
            r'while.*page.*<.*max_pages',
            r'for.*page.*in.*range',
            r'while.*page_num.*<',
            r'while.*current_page.*<',
            r'for.*i.*in.*range.*pages'
        ]
        
        for pattern in pagination_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                audit['has_pagination'] = True
                audit['pagination_patterns'].append(pattern)
                audit['pagination_score'] += 2
                break
        
        # 2. Check for completion validation (2 points)
        completion_patterns = [
            r'total_pages|nbPages|totalCount|total_count',
            r'len\(hits\).*<.*\d+',
            r'not.*hits|not.*vehicles|not.*results',
            r'if.*page.*>=.*total',
            r'break.*# No more'
        ]
        
        for pattern in completion_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                audit['has_completion_check'] = True
                audit['completion_patterns'].append(pattern)
                audit['pagination_score'] += 2
                break
        
        # 3. Check for inventory verification (2 points)
        verification_patterns = [
            r'InventoryVerificationMixin',
            r'verify.*inventory|inventory.*verification',
            r'completeness.*percentage',
            r'expected.*total.*vehicles'
        ]
        
        for pattern in verification_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                audit['has_inventory_verification'] = True
                audit['pagination_score'] += 2
                break
        
        # 4. Check for rate limiting between pages (1 point)
        if re.search(r'time\.sleep|rate_limiter|delay.*page', content, re.IGNORECASE):
            audit['pagination_score'] += 1
        
        # 5. Check for proper error handling in pagination (1 point)
        if re.search(r'try:.*page.*except|except.*page.*error', content, re.IGNORECASE | re.DOTALL):
            audit['pagination_score'] += 1
        
        # 6. Check for max page safety limits (1 point)
        if re.search(r'max_pages.*=.*\d+|page.*<=.*\d+', content, re.IGNORECASE):
            audit['pagination_score'] += 1
        
        # 7. Check for vehicle count logging (1 point)
        if re.search(r'logger.*page.*vehicles|Found.*\d+.*vehicles', content, re.IGNORECASE):
            audit['pagination_score'] += 1
        
        # Determine API type
        if 'algolia' in content.lower(): audit['api_type'] = 'algolia'
        elif 'dealeron' in content.lower(): audit['api_type'] = 'dealeron'
        elif 'ddc' in content.lower(): audit['api_type'] = 'stellantis_ddc'
        elif 'chrome' in content.lower(): audit['api_type'] = 'chrome_driver'
        
        # Generate status and recommendations
        if audit['pagination_score'] >= 8:
            audit['status'] = 'EXCELLENT'
        elif audit['pagination_score'] >= 6:
            audit['status'] = 'GOOD'
        elif audit['pagination_score'] >= 4:
            audit['status'] = 'NEEDS_IMPROVEMENT'
        else:
            audit['status'] = 'CRITICAL_ISSUES'
        
        # Generate specific recommendations
        if not audit['has_pagination']:
            audit['issues'].append('No pagination loop detected')
            audit['recommendations'].append('Implement proper pagination with while/for loop')
        
        if not audit['has_completion_check']:
            audit['issues'].append('No completion validation found')
            audit['recommendations'].append('Add checks for total_pages/empty results')
        
        if not audit['has_inventory_verification']:
            audit['issues'].append('No inventory verification system')
            audit['recommendations'].append('Integrate InventoryVerificationMixin')
        
        return audit
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report"""
        print("📋 PAGINATION AUDIT REPORT")
        print("=" * 50)
        
        total_scrapers = len(self.audit_results)
        excellent = sum(1 for r in self.audit_results.values() if r['pagination_score'] >= 8)
        good = sum(1 for r in self.audit_results.values() if 6 <= r['pagination_score'] < 8)
        needs_work = sum(1 for r in self.audit_results.values() if 4 <= r['pagination_score'] < 6)
        critical = sum(1 for r in self.audit_results.values() if r['pagination_score'] < 4)
        
        print(f"📊 SUMMARY:")
        print(f"   Total Scrapers: {total_scrapers}")
        print(f"   ✅ Excellent (8-10): {excellent} ({excellent/total_scrapers*100:.1f}%)")
        print(f"   ⚠️ Good (6-7): {good} ({good/total_scrapers*100:.1f}%)")
        print(f"   ⚠️ Needs Work (4-5): {needs_work} ({needs_work/total_scrapers*100:.1f}%)")
        print(f"   ❌ Critical (<4): {critical} ({critical/total_scrapers*100:.1f}%)")
        print()
        
        if self.critical_issues:
            print("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in self.critical_issues[:10]:  # Show top 10
                print(f"   ❌ {issue['dealership']}: Score {issue['score']}/10")
                for problem in issue['issues'][:3]:  # Show top 3 issues
                    print(f"      • {problem}")
            print()
        
        # API Type breakdown
        api_types = {}
        for result in self.audit_results.values():
            api_type = result['api_type']
            if api_type not in api_types:
                api_types[api_type] = {'total': 0, 'good': 0}
            api_types[api_type]['total'] += 1
            if result['pagination_score'] >= 6:
                api_types[api_type]['good'] += 1
        
        print("🔧 API TYPE BREAKDOWN:")
        for api_type, stats in api_types.items():
            success_rate = stats['good'] / stats['total'] * 100
            print(f"   {api_type}: {stats['good']}/{stats['total']} ({success_rate:.1f}%) have good pagination")
        print()
        
        # Save detailed report
        self._save_audit_report()
        
        print("💡 RECOMMENDATIONS:")
        print("   1. Focus on critical issues first (score < 4)")
        print("   2. Implement InventoryVerificationMixin in all scrapers")
        print("   3. Add completion validation to all pagination loops")
        print("   4. Ensure rate limiting between page requests")
        print("   5. Add inventory count logging for verification")
        print()
    
    def _save_audit_report(self):
        """Save detailed audit report to JSON file"""
        report_file = f"pagination_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'audit_timestamp': datetime.now().isoformat(),
            'total_scrapers': len(self.audit_results),
            'summary_stats': {
                'excellent': sum(1 for r in self.audit_results.values() if r['pagination_score'] >= 8),
                'good': sum(1 for r in self.audit_results.values() if 6 <= r['pagination_score'] < 8),
                'needs_improvement': sum(1 for r in self.audit_results.values() if 4 <= r['pagination_score'] < 6),
                'critical': sum(1 for r in self.audit_results.values() if r['pagination_score'] < 4)
            },
            'critical_issues': self.critical_issues,
            'detailed_results': self.audit_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file}")
    
    def fix_critical_scrapers(self, dealership_ids: List[str] = None):
        """Generate fixes for critical pagination issues"""
        if dealership_ids is None:
            dealership_ids = [issue['dealership'] for issue in self.critical_issues]
        
        print(f"🔧 GENERATING FIXES FOR {len(dealership_ids)} CRITICAL SCRAPERS")
        print("=" * 60)
        
        for dealership_id in dealership_ids:
            if dealership_id in self.audit_results:
                result = self.audit_results[dealership_id]
                print(f"\n🔧 {dealership_id}:")
                print(f"   Current Score: {result['pagination_score']}/10")
                print(f"   Issues: {', '.join(result['issues'])}")
                print(f"   API Type: {result['api_type']}")
                
                # Generate specific fix code
                self._generate_pagination_fix(dealership_id, result)
    
    def _generate_pagination_fix(self, dealership_id: str, audit_result: Dict):
        """Generate specific pagination fix code for a scraper"""
        api_type = audit_result['api_type']
        
        print(f"   📝 Recommended fix template:")
        
        if api_type == 'algolia':
            print("""
   def _scrape_with_complete_pagination(self, vehicle_type='all'):
       vehicles = []
       page_num = 0
       max_pages = 100  # Safety limit
       
       while page_num < max_pages:
           # Rate limiting
           time.sleep(self.config.request_delay)
           
           # Make API request
           response = self._make_algolia_request(page_num)
           results = response.get('results', [])
           
           if not results:
               break
               
           hits = results[0].get('hits', [])
           total_pages = results[0].get('nbPages', 1)
           
           # Process vehicles
           for vehicle_data in hits:
               vehicle = self._process_vehicle(vehicle_data)
               if vehicle:
                   vehicles.append(vehicle)
           
           # Check completion
           if page_num >= total_pages - 1 or len(hits) < 20:
               break
               
           page_num += 1
           
       return vehicles
            """)
        elif api_type == 'chrome_driver':
            print("""
   def _scrape_with_complete_pagination(self):
       vehicles = []
       page = 1
       max_pages = 50
       
       while page <= max_pages:
           # Navigate to page
           page_url = f"{self.base_url}/inventory?page={page}"
           self.driver.get(page_url)
           
           # Extract vehicles
           page_vehicles = self._extract_vehicles_from_page()
           
           if not page_vehicles:
               break
               
           vehicles.extend(page_vehicles)
           
           # Check for next page
           if not self._has_next_page():
               break
               
           page += 1
           time.sleep(2)  # Rate limiting
           
       return vehicles
            """)

def main():
    """Run comprehensive pagination audit"""
    auditor = PaginationAuditor()
    
    print("🎯 Silver Fox Marketing - Pagination Audit System")
    print("Critical for ensuring complete inventory normalization")
    print()
    
    # Run full audit
    audit_results = auditor.audit_all_scrapers()
    
    # Generate fixes for critical issues
    if auditor.critical_issues:
        auditor.fix_critical_scrapers()
    else:
        print("✅ No critical pagination issues found!")
        print("All scrapers have adequate pagination implementation.")

if __name__ == "__main__":
    main()