#!/usr/bin/env python3
"""
Quick validation of Columbia Honda working scraper
"""

import sys
import os
sys.path.append('scraper')

def quick_validate_columbia_honda():
    """Validate Columbia Honda data accuracy"""
    
    print("🔍 QUICK VALIDATION: Columbia Honda")
    print("Expected: ~298 Honda vehicles (from complete_data.csv)")
    print("=" * 60)
    
    try:
        import importlib
        module = importlib.import_module('dealerships.columbiahonda_working')
        
        # Find scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                hasattr(obj, 'scrape_inventory') and 
                'Scraper' in name and 
                name != 'DealershipScraperBase'):
                scraper_class = obj
                break
        
        if not scraper_class:
            print("❌ No scraper class found")
            return False
        
        config = {
            'name': 'Columbia Honda',
            'base_url': 'https://www.columbiahonda.com'
        }
        
        scraper = scraper_class(config)
        vehicles = scraper.scrape_inventory()
        
        if not vehicles:
            print("❌ No vehicles found")
            return False
        
        print(f"✅ Found {len(vehicles)} vehicles")
        
        # Quick accuracy check on first 5 vehicles
        honda_count = 0
        realistic_prices = 0
        
        for i, vehicle in enumerate(vehicles[:5], 1):
            print(f"\n📋 Vehicle {i}:")
            year = vehicle.get('year', 'N/A')
            make = vehicle.get('make', 'N/A')
            model = vehicle.get('model', 'N/A')
            price = vehicle.get('price', 'N/A')
            vin = vehicle.get('vin', 'N/A')
            
            print(f"   {year} {make} {model} - ${price}")
            if vin and vin != 'N/A':
                print(f"   VIN: {vin[:8]}...")
            
            # Check make
            if str(make).lower() == 'honda':
                honda_count += 1
                print(f"   ✅ Correct make (Honda)")
            else:
                print(f"   ❌ Wrong make: {make}")
            
            # Check price
            try:
                price_num = float(str(price).replace('$', '').replace(',', ''))
                if price_num >= 15000:
                    realistic_prices += 1
                    print(f"   ✅ Realistic price")
                else:
                    print(f"   ❌ Unrealistic price: ${price_num}")
            except:
                print(f"   ⚠️ Cannot parse price: {price}")
        
        accuracy = (honda_count + realistic_prices) / 10 * 100
        
        print(f"\n📊 QUICK ACCURACY CHECK:")
        print(f"   Honda vehicles: {honda_count}/5")
        print(f"   Realistic prices: {realistic_prices}/5")
        print(f"   Accuracy score: {accuracy:.0f}%")
        
        if accuracy >= 80:
            print(f"   ✅ HIGH ACCURACY - Ready for on-lot methodology")
            return True
        else:
            print(f"   ❌ LOW ACCURACY - Needs fixes")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_validate_columbia_honda()
    if success:
        print(f"\n✅ Columbia Honda is ready for on-lot methodology integration")
    else:
        print(f"\n❌ Columbia Honda needs data accuracy fixes first")