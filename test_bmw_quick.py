#!/usr/bin/env python3
"""
Quick BMW scraper test - limited vehicles to validate functionality
"""

import sys
import os
import logging
from pathlib import Path

# Add the scraper path
scraper_path = Path(__file__).parent / "projects/silverfox_scraper_system/silverfox_system/core/scrapers/dealerships"
sys.path.append(str(scraper_path))

# Import the BMW scraper
from bmwofweststlouis_working import BMWofWestStLouisWorkingScraper

def test_bmw_scraper_quick():
    """Quick test of BMW scraper with limited scope"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'bmwofweststlouis',
        'name': 'BMW of West St Louis',
        'base_url': 'https://www.bmwofweststlouis.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 20000, 'max': 200000},
                'year_range': {'min': 2015, 'max': 2025}
            }
        }
    }
    
    # Simple config
    class SimpleConfig:
        request_delay = 1.0  # Faster for testing
        timeout = 15
    
    scraper = BMWofWestStLouisWorkingScraper(config, SimpleConfig())
    
    # Force Chrome mode and limit results
    scraper.use_chrome = True
    
    print("🧪 Quick BMW test - Chrome driver only...")
    
    try:
        # Test just the Chrome scraping method directly
        vehicles = scraper._scrape_with_chrome()
        
        print(f"✅ Found {len(vehicles)} vehicles")
        if vehicles:
            print("📋 First vehicle sample:")
            sample = vehicles[0]
            for key, value in sample.items():
                if value:  # Only show non-empty fields
                    print(f"   {key}: {value}")
        
        return len(vehicles) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bmw_scraper_quick()
    print(f"🎯 BMW scraper test: {'PASSED' if success else 'FAILED'}")