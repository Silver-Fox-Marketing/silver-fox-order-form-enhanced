#!/usr/bin/env python3
"""
Validate data accuracy for remaining working scrapers
Focus on scrapers with high expected inventory counts
"""

import sys
import os
sys.path.append('scraper')
import importlib
import time

def validate_scraper_data(module_name, expected_make, dealership_name, base_url):
    """Validate a single scraper's data accuracy"""
    
    print(f"\n{'='*60}")
    print(f"🔍 VALIDATING: {dealership_name}")
    print(f"Expected make: {expected_make}")
    
    try:
        module = importlib.import_module(f'dealerships.{module_name}')
        
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
            return None
        
        config = {
            'name': dealership_name,
            'base_url': base_url
        }
        
        scraper = scraper_class(config)
        
        start_time = time.time()
        vehicles = scraper.scrape_inventory()
        elapsed = time.time() - start_time
        
        if not vehicles:
            print(f"❌ No vehicles found in {elapsed:.1f}s")
            return {'status': 'failed', 'count': 0, 'accuracy': 0}
        
        print(f"✅ Found {len(vehicles)} vehicles in {elapsed:.1f}s")
        
        # Analyze data accuracy
        correct_make = 0
        realistic_prices = 0
        has_vin = 0
        has_stock = 0
        
        # Sample first 10 vehicles for detailed analysis
        sample_size = min(10, len(vehicles))
        
        for i, vehicle in enumerate(vehicles[:sample_size]):
            # Check make matches expected
            make = str(vehicle.get('make', '')).strip()
            if make.lower() == expected_make.lower():
                correct_make += 1
            
            # Check price reasonableness
            price = vehicle.get('price')
            if price:
                try:
                    price_num = float(str(price).replace('$', '').replace(',', ''))
                    if price_num >= 15000:  # Reasonable minimum
                        realistic_prices += 1
                except:
                    pass
            
            # Check identifiers
            if vehicle.get('vin'):
                has_vin += 1
            if vehicle.get('stock_number'):
                has_stock += 1
        
        # Calculate accuracy metrics
        make_accuracy = (correct_make / sample_size * 100) if sample_size > 0 else 0
        price_accuracy = (realistic_prices / sample_size * 100) if sample_size > 0 else 0
        vin_coverage = (has_vin / sample_size * 100) if sample_size > 0 else 0
        stock_coverage = (has_stock / sample_size * 100) if sample_size > 0 else 0
        
        overall_accuracy = (make_accuracy + price_accuracy) / 2
        
        # Show sample vehicle
        if vehicles:
            sample = vehicles[0]
            print(f"\n📋 Sample vehicle:")
            print(f"   {sample.get('year', 'N/A')} {sample.get('make', 'N/A')} {sample.get('model', 'N/A')}")
            print(f"   Price: ${sample.get('price', 'N/A')}")
            print(f"   VIN: {sample.get('vin', 'N/A')[:8]}..." if sample.get('vin') else "   VIN: N/A")
        
        print(f"\n📊 DATA ACCURACY ANALYSIS:")
        print(f"   Make accuracy: {make_accuracy:.0f}% ({correct_make}/{sample_size} correct)")
        print(f"   Price accuracy: {price_accuracy:.0f}% ({realistic_prices}/{sample_size} realistic)")
        print(f"   VIN coverage: {vin_coverage:.0f}% ({has_vin}/{sample_size} have VINs)")
        print(f"   Stock coverage: {stock_coverage:.0f}% ({has_stock}/{sample_size} have stock)")
        print(f"   Overall accuracy: {overall_accuracy:.0f}%")
        
        if overall_accuracy >= 80:
            print(f"   ✅ HIGH ACCURACY - Ready for on-lot methodology")
            status = 'ready'
        elif overall_accuracy >= 60:
            print(f"   ⚠️ MODERATE ACCURACY - May need fixes")
            status = 'needs_review'
        else:
            print(f"   ❌ LOW ACCURACY - Requires fixes before use")
            status = 'needs_fixes'
        
        return {
            'status': status,
            'count': len(vehicles),
            'accuracy': overall_accuracy,
            'make_accuracy': make_accuracy,
            'price_accuracy': price_accuracy,
            'vin_coverage': vin_coverage
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'status': 'error', 'count': 0, 'accuracy': 0}

def main():
    """Validate remaining working scrapers"""
    
    print("🔍 SYSTEMATIC DATA ACCURACY VALIDATION")
    print("Testing remaining working scrapers for data quality")
    print("Only scrapers with ≥80% accuracy will receive on-lot methodology")
    
    # Priority scrapers based on expected inventory counts
    scrapers_to_test = [
        # High priority (high expected counts from complete_data.csv)
        ('columbiahonda_working', 'Honda', 'Columbia Honda', 'https://www.columbiahonda.com'),
        ('hwkia_working', 'Kia', 'HW Kia', 'https://www.hwkia.com'),
        ('kiaofcolumbia_working', 'Kia', 'Kia of Columbia', 'https://www.kiaofcolumbia.com'),
        ('bmwofweststlouis_working', 'BMW', 'BMW of West St Louis', 'https://www.bmwofweststlouis.com'),
        
        # Medium priority
        ('miniofstlouis_working', 'MINI', 'MINI of St Louis', 'https://www.miniofstlouis.com'),
        ('rustydrewingcadillac_working', 'Cadillac', 'Rusty Drewing Cadillac', 'https://www.rustydrewingcadillac.com'),
        ('frankletahonda_working', 'Honda', 'Frank Leta Honda', 'https://www.frankletahonda.com'),
        ('suntrupkiasouth_working', 'Kia', 'Suntrup Kia South', 'https://www.suntrupkiasouth.com'),
    ]
    
    results = {
        'ready': [],
        'needs_review': [],
        'needs_fixes': [],
        'failed': [],
        'error': []
    }
    
    for module_name, expected_make, dealership_name, base_url in scrapers_to_test:
        result = validate_scraper_data(module_name, expected_make, dealership_name, base_url)
        
        if result:
            status = result['status']
            results[status].append({
                'dealership': dealership_name,
                'module': module_name,
                'count': result['count'],
                'accuracy': result.get('accuracy', 0)
            })
    
    # Generate summary report
    print(f"\n{'='*60}")
    print(f"📊 VALIDATION SUMMARY REPORT")
    print(f"{'='*60}")
    
    print(f"\n✅ READY FOR ON-LOT METHODOLOGY ({len(results['ready'])} scrapers):")
    for item in results['ready']:
        print(f"   • {item['dealership']}: {item['count']} vehicles, {item['accuracy']:.0f}% accuracy")
    
    if results['needs_review']:
        print(f"\n⚠️ NEEDS REVIEW ({len(results['needs_review'])} scrapers):")
        for item in results['needs_review']:
            print(f"   • {item['dealership']}: {item['count']} vehicles, {item['accuracy']:.0f}% accuracy")
    
    if results['needs_fixes']:
        print(f"\n❌ NEEDS FIXES ({len(results['needs_fixes'])} scrapers):")
        for item in results['needs_fixes']:
            print(f"   • {item['dealership']}: {item['count']} vehicles, {item['accuracy']:.0f}% accuracy")
    
    if results['failed']:
        print(f"\n❌ FAILED ({len(results['failed'])} scrapers):")
        for item in results['failed']:
            print(f"   • {item['dealership']}: No vehicles found")
    
    if results['error']:
        print(f"\n❌ ERRORS ({len(results['error'])} scrapers):")
        for item in results['error']:
            print(f"   • {item['dealership']}: Scraper error")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Apply on-lot methodology to {len(results['ready'])} ready scrapers")
    print(f"2. Review and fix {len(results['needs_review'])} moderate accuracy scrapers")
    print(f"3. Fix critical issues in {len(results['needs_fixes']) + len(results['failed']) + len(results['error'])} broken scrapers")

if __name__ == "__main__":
    main()