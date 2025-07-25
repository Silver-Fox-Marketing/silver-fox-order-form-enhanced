#!/usr/bin/env python3
"""
Dave Sinclair Lincoln St. Peters Scraper
========================================

DealerOn Cosmos-based scraper following proven patterns.
Platform: dealeron_cosmos
Generated: 2025-07-24
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class DavesinclairlincolnstpetersWorkingScraper:
    """Scraper for Dave Sinclair Lincoln St. Peters"""
    
    def __init__(self):
        self.base_url = "https://www.davesinclairlincolnstpeters.com"
        self.dealer_name = "Dave Sinclair Lincoln St. Peters"
        self.logger = logging.getLogger(__name__)
        
        # DealerOn API endpoints
        self.api_endpoints = {
            'search': f"{self.base_url}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_ALL:inventory-data-bus1/getInventory",
            'details': f"{self.base_url}/apis/widget/INVENTORY_DETAIL_DEFAULT_AUTO:inventory-detail1/getInventoryDetail"
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': self.base_url
        }
        
        self.processed_vehicles = set()
    
    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Main entry point - get all vehicles"""
        all_vehicles = []
        
        try:
            # Get vehicles via DealerOn API
            vehicles = self._get_vehicles_via_api()
            
            if vehicles:
                all_vehicles.extend(vehicles)
                self.logger.info(f"✅ Found {len(vehicles)} vehicles via DealerOn API")
            else:
                self.logger.warning("⚠️ No vehicles found")
                
        except Exception as e:
            self.logger.error(f"❌ Error getting vehicles: {e}")
        
        return all_vehicles
    
    def _get_vehicles_via_api(self) -> List[Dict[str, Any]]:
        """Get vehicles using DealerOn API"""
        vehicles = []
        start = 0
        count = 50
        
        while True:
            try:
                params = {
                    'start': start,
                    'count': count,
                    'sort': 'price|asc',
                    'showFacetCounts': 'true',
                    'facets': 'type|make|model|year',
                    'originalParams': 'inventory-listing'
                }
                
                response = requests.get(
                    self.api_endpoints['search'],
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"API error: {response.status_code}")
                    break
                
                data = response.json()
                inventory = data.get('inventory', [])
                
                if not inventory:
                    break
                
                # Process each vehicle
                for vehicle_data in inventory:
                    vehicle = self._process_dealeron_vehicle(vehicle_data)
                    if vehicle and vehicle['vin'] not in self.processed_vehicles:
                        vehicles.append(vehicle)
                        self.processed_vehicles.add(vehicle['vin'])
                
                # Check if more pages
                total_count = data.get('totalCount', 0)
                if start + count >= total_count:
                    break
                
                start += count
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error fetching vehicles at start={start}: {e}")
                break
        
        return vehicles
    
    def _process_dealeron_vehicle(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process DealerOn vehicle data"""
        try:
            vehicle = {
                'vin': data.get('vin', '').strip(),
                'stock_number': data.get('stockNumber', '').strip(),
                'year': int(data.get('year', 0)),
                'make': data.get('make', '').strip(),
                'model': data.get('model', '').strip(),
                'trim': data.get('trim', '').strip(),
                'price': self._parse_price(data.get('internetPrice') or data.get('price')),
                'msrp': self._parse_price(data.get('msrp')),
                'mileage': int(data.get('mileage', 0)),
                'exterior_color': data.get('exteriorColor', '').strip(),
                'interior_color': data.get('interiorColor', '').strip(),
                'fuel_type': data.get('fuelType', '').strip(),
                'transmission': data.get('transmission', '').strip(),
                'condition': data.get('type', 'used').lower(),
                'url': data.get('link', ''),
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
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        if numbers:
            return int(numbers[0])
        
        return None


# Test function
def test_scraper():
    """Test the scraper"""
    logging.basicConfig(level=logging.INFO)
    scraper = DavesinclairlincolnstpetersWorkingScraper()
    vehicles = scraper.get_all_vehicles()
    print(f"Found {len(vehicles)} vehicles")
    return vehicles


if __name__ == "__main__":
    test_scraper()
