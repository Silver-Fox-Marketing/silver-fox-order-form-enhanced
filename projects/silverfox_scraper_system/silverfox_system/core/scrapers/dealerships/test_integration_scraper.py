#!/usr/bin/env python3
"""
Test Integration Scraper
========================

Simple test scraper to verify the integration is working without
external dependencies or complex API calls.
"""

import random
from datetime import datetime
from typing import Dict, List, Any

class TestIntegrationScraper:
    """Simple test scraper to verify integration works"""
    
    def __init__(self):
        self.dealer_name = "Test Integration Dealer"
    
    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Generate test vehicles to verify integration"""
        
        # Generate 5 test vehicles with unique data each time
        vehicles = []
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        for i in range(5):
            vehicle = {
                'vin': f'TEST{timestamp.replace(":", "")}{i:03d}',
                'stock_number': f'TST{i:06d}',
                'condition': 'new',
                'year': 2025,
                'make': 'Test',
                'model': f'Model_{timestamp}_{i}',
                'trim': 'Integration',
                'exterior_color': random.choice(['Blue', 'Red', 'Green', 'Yellow', 'Purple']),
                'interior_color': 'Black',
                'status': 'Available',
                'price': random.randint(25000, 45000),
                'msrp': random.randint(27000, 48000),
                'mileage': 0,
                'body_style': 'Sedan',
                'fuel_type': 'Electric',
                'transmission': 'Automatic',
                'date_in_stock': datetime.now().strftime('%Y-%m-%d'),
                'street_address': '123 Test Drive',
                'locality': 'Test City',
                'postal_code': '12345',
                'region': 'TS',
                'country': 'US',
                'location': 'Test Integration Dealer',
                'dealer_name': self.dealer_name,
                'url': f'https://testdealer.com/vehicle-{i}',
                'scraped_at': datetime.now().isoformat(),
                'data_source': 'real_integration_test'
            }
            vehicles.append(vehicle)
        
        print(f"Test scraper generated {len(vehicles)} vehicles at {timestamp}")
        return vehicles

def test_scraper():
    """Test function"""
    scraper = TestIntegrationScraper()
    vehicles = scraper.get_all_vehicles()
    print(f"Generated {len(vehicles)} test vehicles")
    if vehicles:
        print(f"Sample vehicle: {vehicles[0]['year']} {vehicles[0]['make']} {vehicles[0]['model']}")
    return vehicles

if __name__ == "__main__":
    test_scraper()