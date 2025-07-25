#!/usr/bin/env python3
"""
Frank Leta Honda Scraper
========================

Algolia-based scraper following proven BMW pattern.
Platform: algolia
Generated: 2025-07-24
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class FrankletahondaWorkingScraper:
    """Scraper for Frank Leta Honda"""
    
    def __init__(self):
        self.base_url = "https://www.frankletahonda.com"
        self.dealer_name = "Frank Leta Honda"
        self.logger = logging.getLogger(__name__)
        
        # Algolia configuration
        self.api_config = {
            'app_id': "YAUO1QHBQ9",
            'api_key': "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
            'index_name': "prod_STITCHED_vehicle_search_feeds",
            'endpoint': "https://yauo1qhbq9-dsn.algolia.net/1/indexes/prod_STITCHED_vehicle_search_feeds/query"
        }
        
        self.headers = {
            'X-Algolia-API-Key': self.api_config['api_key'],
            'X-Algolia-Application-Id': self.api_config['app_id'],
            'Content-Type': 'application/json'
        }
        
        self.processed_vehicles = set()
    
    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Main entry point - get all vehicles following BMW pattern"""
        all_vehicles = []
        
        try:
            # Try API approach first
            vehicles = self._get_vehicles_via_api()
            
            if vehicles:
                all_vehicles.extend(vehicles)
                self.logger.info(f"✅ Found {len(vehicles)} vehicles via Algolia API")
            else:
                self.logger.warning("⚠️ No vehicles found via API")
                
        except Exception as e:
            self.logger.error(f"❌ Error getting vehicles: {e}")
        
        return all_vehicles
    
    def _get_vehicles_via_api(self) -> List[Dict[str, Any]]:
        """Get vehicles using Algolia API"""
        vehicles = []
        page = 0
        items_per_page = 20
        
        while True:
            try:
                # Build request payload
                payload = {
                    "query": "",
                    "hitsPerPage": items_per_page,
                    "page": page,
                    "facetFilters": ["searchable_dealer_name:Frank Leta Honda"]
                }
                
                response = requests.post(
                    self.api_config['endpoint'],
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"API error: {response.status_code}")
                    break
                
                data = response.json()
                hits = data.get('hits', [])
                
                if not hits:
                    break
                
                # Process each vehicle
                for hit in hits:
                    vehicle = self._process_algolia_vehicle(hit)
                    if vehicle and vehicle['vin'] not in self.processed_vehicles:
                        vehicles.append(vehicle)
                        self.processed_vehicles.add(vehicle['vin'])
                
                # Check if more pages
                if len(hits) < items_per_page:
                    break
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
        
        return vehicles
    
    def _process_algolia_vehicle(self, hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Algolia hit into standard vehicle format"""
        try:
            vehicle = {
                'vin': hit.get('vin', '').strip(),
                'stock_number': hit.get('stock_number', '').strip(),
                'year': int(hit.get('year', 0)),
                'make': hit.get('make', '').strip(),
                'model': hit.get('model', '').strip(),
                'trim': hit.get('trim', '').strip(),
                'price': self._parse_price(hit.get('price')),
                'msrp': self._parse_price(hit.get('msrp')),
                'mileage': int(hit.get('mileage', 0)),
                'exterior_color': hit.get('exterior_color', '').strip(),
                'interior_color': hit.get('interior_color', '').strip(),
                'fuel_type': hit.get('fuel_type', '').strip(),
                'transmission': hit.get('transmission', '').strip(),
                'condition': hit.get('type', 'used').lower(),
                'url': hit.get('url', ''),
                'dealer_name': self.dealer_name,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Validate required fields
            if not vehicle['vin'] or not vehicle['year']:
                return None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error processing vehicle: {e}")
            return None
    
    def _parse_price(self, price_value: Any) -> Optional[int]:
        """Parse price from various formats"""
        if not price_value:
            return None
        
        if isinstance(price_value, (int, float)):
            return int(price_value)
        
        # Handle string prices
        price_str = str(price_value).lower().strip()
        if 'call' in price_str or 'contact' in price_str:
            return None
        
        # Extract numeric value
        import re
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        if numbers:
            return int(numbers[0])
        
        return None


# Test function for standalone execution
def test_scraper():
    """Test the scraper"""
    logging.basicConfig(level=logging.INFO)
    scraper = FrankletahondaWorkingScraper()
    vehicles = scraper.get_all_vehicles()
    print(f"Found {len(vehicles)} vehicles")
    return vehicles


if __name__ == "__main__":
    test_scraper()
