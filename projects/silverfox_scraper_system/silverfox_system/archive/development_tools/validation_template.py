#!/usr/bin/env python3
"""
Data Accuracy Validation Template
Copy and modify for each scraper
"""

def validate_scraper_data(module_name, expected_make, dealership_name, base_url):
    """Validate scraper data accuracy"""
    
    print(f"🔍 DATA ACCURACY VALIDATION: {dealership_name}")
    print(f"Checking if scraped data matches expected {expected_make} vehicles")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append('scraper')
        import importlib
        
        module = importlib.import_module(f'dealerships.{module_name}')
        
        # Find scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                hasattr(obj, 'scrape_inventory') and 
                'Scraper' in name):
                scraper_class = obj
                break
        
        if not scraper_class:
            print("❌ No scraper class found")
            return False
        
        config = {
            'name': dealership_name,
            'base_url': base_url
        }
        
        scraper = scraper_class(config)
        vehicles = scraper.scrape_inventory()
        
        print(f"📊 Found {len(vehicles)} vehicles")
        
        if not vehicles:
            print("❌ No vehicles to validate")
            return False
        
        # Test first 5 vehicles for data accuracy
        correct_make = 0
        realistic_prices = 0
        
        for i, vehicle in enumerate(vehicles[:5], 1):
            year = vehicle.get('year', 'N/A')
            make = vehicle.get('make', 'N/A')
            model = vehicle.get('model', 'N/A')
            price = vehicle.get('price', 'N/A')
            vin = vehicle.get('vin', 'N/A')
            
            print(f"\n   Vehicle {i}: {year} {make} {model} - ${price}")
            
            # Check make matches expected
            if str(make).lower() == expected_make.lower():
                print(f"   ✅ Make matches expected ({expected_make})")
                correct_make += 1
            else:
                print(f"   ❌ Make mismatch: Expected {expected_make}, got {make}")
            
            # Check price reasonableness
            if price and price != 'N/A':
                try:
                    price_num = float(str(price).replace('$', '').replace(',', ''))
                    if price_num >= 15000:
                        print(f"   ✅ Price appears realistic")
                        realistic_prices += 1
                    else:
                        print(f"   ❌ Price unrealistic: ${price_num}")
                except:
                    print(f"   ⚠️ Could not parse price: {price}")
        
        accuracy_score = ((correct_make + realistic_prices) / 10) * 100
        print(f"\n📊 DATA ACCURACY: {accuracy_score:.1f}%")
        
        return accuracy_score >= 80
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

# Example usage:
# validate_scraper_data('columbiahonda_working', 'Honda', 'Columbia Honda', 'https://www.columbiahonda.com')
