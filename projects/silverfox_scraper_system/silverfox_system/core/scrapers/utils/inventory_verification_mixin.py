#!/usr/bin/env python3
"""
Inventory Verification Mixin
Provides inventory verification capabilities for scrapers
"""

import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class InventoryVerificationMixin:
    """Mixin class providing inventory verification functionality"""
    
    def _get_expected_inventory_totals(self) -> Dict[str, int]:
        """Get expected inventory totals from dealer website"""
        try:
            # Try to get totals from main inventory page
            inventory_url = getattr(self, 'inventory_url', '') or self.dealership_config.get('base_url', '')
            
            if not inventory_url:
                return {'new': 0, 'used': 0, 'total': 0}
            
            response = requests.get(inventory_url, timeout=10)
            if response.status_code == 200:
                # Simple pattern matching for common inventory count patterns
                content = response.text.lower()
                
                # Look for number patterns near inventory keywords
                import re
                patterns = [
                    r'(\d+)\s+(?:new|used)?\s*(?:vehicles?|cars?|inventory)',
                    r'(?:showing|found|available)\s+(\d+)',
                    r'(\d+)\s+(?:results?|matches?)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        total = max(int(match) for match in matches)
                        return {'new': total // 2, 'used': total // 2, 'total': total}
                
            return {'new': 0, 'used': 0, 'total': 0}
            
        except Exception as e:
            self.logger.warning(f"Failed to get expected totals: {e}")
            return {'new': 0, 'used': 0, 'total': 0}
    
    def _verify_inventory_completeness(self, vehicles: List[Dict], expected: Dict[str, int]) -> Dict[str, Any]:
        """Verify scraped inventory against expected totals"""
        scraped_total = len(vehicles)
        expected_total = expected.get('total', 0)
        
        completeness = (scraped_total / expected_total * 100) if expected_total > 0 else 100
        
        return {
            'scraped_count': scraped_total,
            'expected_count': expected_total,
            'completeness_percentage': min(completeness, 100),
            'verification_status': 'complete' if completeness >= 90 else 'partial' if completeness >= 50 else 'incomplete'
        }
    
    def verify_against_dealer_website(self, scraped_count: int) -> Dict[str, Any]:
        """Verify scraped data against dealer website"""
        try:
            # Get expected totals
            expected = self._get_expected_inventory_totals()
            
            # Calculate verification metrics
            verification = {
                'scraped_vehicles': scraped_count,
                'expected_vehicles': expected.get('total', 0),
                'verification_timestamp': datetime.now().isoformat(),
                'verification_method': 'website_comparison'
            }
            
            if expected.get('total', 0) > 0:
                coverage = (scraped_count / expected['total']) * 100
                verification['coverage_percentage'] = min(coverage, 100)
                verification['status'] = 'verified' if coverage >= 80 else 'partial' if coverage >= 50 else 'low_coverage'
            else:
                verification['coverage_percentage'] = 100
                verification['status'] = 'no_baseline'
            
            return verification
            
        except Exception as e:
            return {
                'scraped_vehicles': scraped_count,
                'error': str(e),
                'status': 'error',
                'verification_timestamp': datetime.now().isoformat()
            }
    
    def _report_inventory_verification(self, verification: Dict[str, Any]):
        """Report inventory verification results"""
        print("\n📊 INVENTORY VERIFICATION REPORT")
        print("=" * 50)
        
        scraped = verification.get('scraped_totals', {}).get('scraped_count', 0)
        expected = verification.get('scraped_totals', {}).get('expected_count', 0)
        completeness = verification.get('completeness_percentage', 0)
        
        print(f"📥 Scraped vehicles: {scraped}")
        print(f"🎯 Expected vehicles: {expected}")
        print(f"📈 Completeness: {completeness:.1f}%")
        
        if completeness >= 90:
            print("✅ EXCELLENT: High completeness achieved")
        elif completeness >= 70:
            print("⚠️ GOOD: Acceptable completeness")
        elif completeness >= 50:
            print("⚠️ MODERATE: Partial inventory captured") 
        else:
            print("❌ LOW: Significant inventory missing")
        
        # Website verification
        website_verification = verification.get('website_verification', {})
        if 'coverage_percentage' in website_verification:
            coverage = website_verification['coverage_percentage']
            print(f"🌐 Website coverage: {coverage:.1f}%")
