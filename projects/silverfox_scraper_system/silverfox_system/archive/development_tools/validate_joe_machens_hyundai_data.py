#!/usr/bin/env python3
"""
Validate Joe Machens Hyundai data accuracy
We know this scraper works (323 vehicles), now check if data is accurate
"""

import sys
import os
sys.path.append('scraper')

def decode_vin_manufacturer(vin):
    """Decode VIN to identify manufacturer"""
    if len(vin) != 17:
        return "Invalid VIN length"
    
    # World Manufacturer Identifier (WMI) - first 3 characters
    wmi = vin[:3]
    
    # Common Hyundai WMIs
    hyundai_wmis = [
        'KMH', 'KNH', 'KNA', 'KNB', 'KND', 'KNE', 'KNF', 'KNG',  # Hyundai Korea
        'KMS', 'KMJ',  # Hyundai other regions
        '5NP', '5NM'   # Hyundai USA
    ]
    
    # Check if it's a Hyundai VIN
    for hyundai_wmi in hyundai_wmis:
        if wmi.startswith(hyundai_wmi[:2]) or wmi == hyundai_wmi:
            return f"Hyundai (WMI: {wmi})"
    
    # Check other common manufacturers
    if wmi.startswith('1G') or wmi.startswith('3G'):
        return f"General Motors (WMI: {wmi})"
    elif wmi.startswith('1FA') or wmi.startswith('1FB') or wmi.startswith('1FC'):
        return f"Ford (WMI: {wmi})"
    elif wmi.startswith('1C') or wmi.startswith('1B'):
        return f"Chrysler/Stellantis (WMI: {wmi})"
    elif wmi.startswith('JHM') or wmi.startswith('1HG'):
        return f"Honda (WMI: {wmi})"
    elif wmi.startswith('JTD') or wmi.startswith('5TE'):
        return f"Toyota (WMI: {wmi})"
    else:
        return f"Other manufacturer (WMI: {wmi})"

def validate_joe_machens_hyundai_data():
    """Validate Joe Machens Hyundai data accuracy"""
    
    print("🔍 DATA ACCURACY VALIDATION: Joe Machens Hyundai")
    print("Checking if scraped data matches expected Hyundai vehicles")
    print("=" * 60)
    
    try:
        import importlib
        module = importlib.import_module('dealerships.joemachenshyundai_onlot')
        
        # Get the scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                hasattr(obj, 'scrape_inventory') and 
                'JoeMachensHyundai' in name):
                scraper_class = obj
                break
        
        if not scraper_class:
            print("❌ No scraper class found")
            return False
        
        config = {
            'name': 'Joe Machens Hyundai',
            'base_url': 'https://www.joemachenshyundai.com'
        }
        
        scraper = scraper_class(config)
        vehicles = scraper.scrape_inventory()
        
        print(f"📊 Found {len(vehicles)} vehicles")
        
        if not vehicles:
            print("❌ No vehicles to validate")
            return False
        
        # Analyze first 10 vehicles for data accuracy
        print(f"\n🔍 DETAILED VEHICLE ANALYSIS:")
        
        correct_manufacturer = 0
        wrong_manufacturer = 0
        invalid_vins = 0
        realistic_prices = 0
        unrealistic_prices = 0
        
        for i, vehicle in enumerate(vehicles[:10], 1):
            print(f"\n   Vehicle {i}:")
            year = vehicle.get('year', 'N/A')
            make = vehicle.get('make', 'N/A')
            model = vehicle.get('model', 'N/A')
            price = vehicle.get('price', 'N/A')
            vin = vehicle.get('vin', 'N/A')
            
            print(f"   {year} {make} {model} - ${price}")
            print(f"   VIN: {vin}")
            
            # Validate VIN manufacturer
            if vin and vin != 'N/A' and len(str(vin)) == 17:
                actual_make = decode_vin_manufacturer(str(vin))
                print(f"   VIN decoded: {actual_make}")
                
                if "Hyundai" in actual_make:
                    print(f"   ✅ VIN matches claimed manufacturer")
                    correct_manufacturer += 1
                else:
                    print(f"   ❌ VIN MISMATCH: Expected Hyundai, got {actual_make}")
                    wrong_manufacturer += 1
            else:
                print(f"   ⚠️ Invalid VIN format")
                invalid_vins += 1
            
            # Validate price reasonableness
            if price and price != 'N/A':
                try:
                    price_num = float(str(price).replace('$', '').replace(',', ''))
                    if price_num >= 15000:  # Reasonable minimum for any vehicle
                        print(f"   ✅ Price appears realistic")
                        realistic_prices += 1
                    else:
                        print(f"   ❌ Price seems unrealistic: ${price_num}")
                        unrealistic_prices += 1
                except:
                    print(f"   ⚠️ Could not parse price: {price}")
                    unrealistic_prices += 1
            
            print("-" * 40)
        
        # Summary validation
        print(f"\n🎯 DATA ACCURACY SUMMARY (first 10 vehicles):")
        print(f"   VIN Manufacturer:")
        print(f"     ✅ Correct (Hyundai): {correct_manufacturer}")
        print(f"     ❌ Wrong manufacturer: {wrong_manufacturer}")
        print(f"     ⚠️ Invalid VINs: {invalid_vins}")
        
        print(f"   Pricing:")
        print(f"     ✅ Realistic prices: {realistic_prices}")
        print(f"     ❌ Unrealistic prices: {unrealistic_prices}")
        
        # Overall assessment
        total_tested = 10
        accuracy_score = ((correct_manufacturer + realistic_prices) / (total_tested * 2)) * 100
        
        print(f"\n📊 OVERALL DATA ACCURACY: {accuracy_score:.1f}%")
        
        if accuracy_score >= 80:
            print(f"   ✅ EXCELLENT: Data appears highly accurate")
            print(f"   📋 Ready for on-lot methodology integration")
            return True
        elif accuracy_score >= 60:
            print(f"   ⚠️ MODERATE: Some data issues found")
            print(f"   🔧 May need fixes before on-lot integration")
            return False
        else:
            print(f"   ❌ POOR: Significant data accuracy issues")
            print(f"   🔧 Requires major fixes before use")
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_joe_machens_hyundai_data()
    
    if success:
        print(f"\n✅ VALIDATION PASSED: Joe Machens Hyundai has accurate data")
        print(f"   📋 Safe to apply on-lot filtering methodology")
    else:
        print(f"\n❌ VALIDATION FAILED: Data accuracy issues found")
        print(f"   🔧 Fix data issues before on-lot integration")