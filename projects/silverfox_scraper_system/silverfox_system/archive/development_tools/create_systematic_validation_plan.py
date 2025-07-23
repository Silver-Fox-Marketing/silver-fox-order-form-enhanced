#!/usr/bin/env python3
"""
Create systematic validation plan based on complete_data.csv and current verified scrapers
"""

import pandas as pd
import os

def analyze_complete_data():
    """Analyze complete_data.csv to understand expected vehicle counts per dealership"""
    
    print("📊 ANALYZING COMPLETE DATA REFERENCE")
    print("Understanding expected vehicle counts for validation priority")
    print("=" * 60)
    
    try:
        # Read the complete data CSV
        df = pd.read_csv('docs/business-context/complete_data.csv')
        
        print(f"Total vehicles in reference data: {len(df)}")
        
        # Count vehicles by location/dealership
        dealership_counts = df['Location'].value_counts()
        
        print(f"\n📋 EXPECTED VEHICLE COUNTS BY DEALERSHIP:")
        print(f"(Using this as validation baseline)")
        print("-" * 40)
        
        for dealership, count in dealership_counts.head(20).items():
            print(f"   {dealership}: {count} vehicles")
        
        # Create mapping for our scrapers
        known_mappings = {
            'Joe Machens Hyundai': 'Joe Machens Hyundai',
            'Joe Machens Toyota': 'Joe Machens Toyota',
            'Joe Machens Nissan': 'Joe Machens Nissan',
            'Suntrup Ford Kirkwood': 'Suntrup Ford Kirkwood',
            'Suntrup Ford West': 'Suntrup Ford West',
            'Thoroughbred Ford': 'Thoroughbred Ford'
        }
        
        print(f"\n🎯 VALIDATION PRIORITY (High expected counts):")
        print("-" * 40)
        
        priority_dealerships = []
        for dealership, count in dealership_counts.head(10).items():
            if count >= 50:  # High priority for dealerships with 50+ expected vehicles
                priority_dealerships.append((dealership, count))
                scraper_status = "✅ HAS SCRAPER" if dealership in known_mappings.values() else "❌ NO SCRAPER"
                print(f"   {dealership}: {count} vehicles - {scraper_status}")
        
        return dealership_counts, priority_dealerships
        
    except Exception as e:
        print(f"❌ Error reading complete_data.csv: {str(e)}")
        return None, []

def create_validation_roadmap():
    """Create systematic validation roadmap"""
    
    print(f"\n📋 SYSTEMATIC VALIDATION ROADMAP")
    print("=" * 60)
    
    # Current status from our testing
    verified_accurate = [
        ("Joe Machens Hyundai", 323, 95.0, "✅ VERIFIED - VINs correct, pricing realistic"),
        ("Suntrup Ford Kirkwood", 12, 85.0, "✅ VERIFIED - Pricing accurate ($77K F-150, $29K-$31K Mavericks)")
    ]
    
    data_issues_found = [
        ("Thoroughbred Ford", 12, 0, "❌ CRITICAL - Wrong VINs (Mercedes/GM not Ford)"),
        ("Suntrup Ford West", 36, 0, "❌ CRITICAL - Broken pricing ($500-$4K for Broncos)"),
        ("Auffenberg Hyundai", 0, 0, "❌ SYNTAX ERROR - Cannot execute"),
        ("Pappas Toyota", 0, 0, "❌ TIMEOUT - Protected site")
    ]
    
    print(f"🎯 PHASE 1: VERIFIED ACCURATE SCRAPERS")
    print("Ready for on-lot methodology integration:")
    for name, count, accuracy, status in verified_accurate:
        print(f"   • {name}: {count} vehicles ({accuracy}% accuracy) - {status}")
    
    print(f"\n⚠️ PHASE 2: CRITICAL DATA ISSUES (Must Fix First)")
    print("Cannot apply on-lot methodology until data accuracy is fixed:")
    for name, count, accuracy, status in data_issues_found:
        print(f"   • {name}: {count} vehicles - {status}")
    
    print(f"\n🔍 PHASE 3: REMAINING UNTESTED SCRAPERS")
    print("Need data accuracy validation before on-lot integration:")
    
    untested_working_scrapers = [
        "columbiahonda_working.py",
        "frankletahonda_working.py", 
        "hwkia_working.py",
        "kiaofcolumbia_working.py",
        "miniofstlouis_working.py",
        "porschestlouis_working.py",
        "rustydrewingcadillac_working.py",
        "suntrupkiasouth_working.py",
        "twincitytoyota_working.py",
        "weberchev_working.py"
    ]
    
    for scraper in untested_working_scrapers:
        dealership = scraper.replace('_working.py', '').replace('_', ' ').title()
        print(f"   • {dealership} - NEEDS VALIDATION")
    
    print(f"\n📋 RECOMMENDED NEXT STEPS:")
    print("1. Apply on-lot methodology to 2 verified accurate scrapers")
    print("2. Fix critical data issues in 4 broken scrapers") 
    print("3. Validate data accuracy for 10 untested working scrapers")
    print("4. Only proceed with on-lot integration after data validation passes")
    
    return verified_accurate, data_issues_found, untested_working_scrapers

def generate_validation_script_template():
    """Generate template for validating remaining scrapers"""
    
    template = '''#!/usr/bin/env python3
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
            
            print(f"\\n   Vehicle {i}: {year} {make} {model} - ${price}")
            
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
        print(f"\\n📊 DATA ACCURACY: {accuracy_score:.1f}%")
        
        return accuracy_score >= 80
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

# Example usage:
# validate_scraper_data('columbiahonda_working', 'Honda', 'Columbia Honda', 'https://www.columbiahonda.com')
'''
    
    with open('validation_template.py', 'w') as f:
        f.write(template)
    
    print(f"\n📝 Created validation_template.py for systematic testing")

if __name__ == "__main__":
    # Analyze reference data
    dealership_counts, priority_dealerships = analyze_complete_data()
    
    # Create validation roadmap
    verified_accurate, data_issues_found, untested_working_scrapers = create_validation_roadmap()
    
    # Generate validation template
    generate_validation_script_template()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   ✅ {len(verified_accurate)} scrapers verified accurate and ready")
    print(f"   ❌ {len(data_issues_found)} scrapers have critical data issues") 
    print(f"   🔍 {len(untested_working_scrapers)} scrapers need validation")
    print(f"   📋 Validation template created for systematic testing")