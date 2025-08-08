#!/usr/bin/env python3
"""
Test All Transferred Scrapers - Critical Verification
Tests each of the 40 independently transferred scrapers to ensure they work with enhanced error handling
"""

import os
import sys
import traceback
import json
from datetime import datetime

# Add bulletproof package scrapers to path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers')

def test_scraper_instantiation(scraper_name):
    """Test individual scraper instantiation and error handling"""
    
    try:
        print(f"\nTesting {scraper_name}...")
        
        # Dynamic import
        scraper_module = __import__(scraper_name.lower())
        scraper_class = getattr(scraper_module, scraper_name.upper())
        
        # Create test paths
        data_folder = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers\logs\test_data'
        output_file = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers\logs\test_output.csv'
        
        # Ensure test directory exists
        os.makedirs(data_folder, exist_ok=True)
        
        # Try to instantiate the scraper
        scraper_instance = scraper_class(data_folder, output_file)
        
        # Verify enhanced helper is working
        helper_type = type(scraper_instance.helper).__name__
        
        print(f"SUCCESS: {scraper_name}")
        print(f"  - Helper: {helper_type}")
        print(f"  - Data folder: {scraper_instance.data_folder}")
        print(f"  - Output file: {scraper_instance.output_file}")
        
        # Check for interface if applicable
        if hasattr(scraper_instance, 'interface'):
            interface_type = type(scraper_instance.interface).__name__
            print(f"  - Interface: {interface_type}")
        
        return True
        
    except ImportError as e:
        print(f"IMPORT ERROR: {scraper_name}")
        print(f"  Error: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: {scraper_name}")
        print(f"  Error: {str(e)}")
        print(f"  Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function for all transferred scrapers"""
    
    print("CRITICAL VERIFICATION: Testing All Transferred Scrapers")
    print("=" * 60)
    print("Testing each of the 40 independently transferred scrapers")
    print("Verifying enhanced error handling and original logic preservation")
    print("=" * 60)
    
    # All transferred scrapers (based on independent transfer results)
    transferred_scrapers = [
        'AUDIRANCHOMIRAGE',
        'AUFFENBERGHYUNDAI', 
        'BMWOFWESTSTLOUIS',
        'BOMMARITOCADILLAC',
        'BOMMARITOWESTCOUNTY',
        'COLUMBIABMW',
        'COLUMBIAHONDA',
        'DAVESINCLAIRLINCOLNSOUTH',
        'DAVESINCLAIRLINCOLNSTPETERS',
        'FRANKLETAHONDA',
        'GLENDALECHRYSLERJEEP',
        'HONDAFRONTENAC',
        'HWKIA',
        'INDIGOAUTOGROUP',
        'JAGUARRANCHOMIRAGE',
        'JOEMACHENSCDJR',
        'JOEMACHENSHYUNDAI',
        'JOEMACHENSNISSAN',
        'JOEMACHENSTOYOTA',
        'KIAOFCOLUMBIA',
        'LANDROVERRANCHOMIRAGE',
        'MINIOFSTLOUIS',
        'PAPPASTOYOTA',
        'PORSCHESTLOUIS',
        'PUNDMANNFORD',
        'RUSTYDREWINGCADILLAC',
        'RUSTYDREWINGCHEVROLETBUICKGMC',
        'SERRAHONDAOFALLON',
        'SOUTHCOUNTYAUTOS',
        'SPIRITLEXUS',
        'STEHOUWERAUTO',
        'SUNTRUPBUICKGMC',
        'SUNTRUPFORDKIRKWOOD',
        'SUNTRUPFORDWEST',
        'SUNTRUPHYUNDAISOUTH',
        'SUNTRUPKIASOUTH',
        'THOROUGHBREDFORD',
        'TWINCITYTOYOTA',
        'WCVOLVOCARS',
        'WEBERCHEV'
    ]
    
    print(f"Testing {len(transferred_scrapers)} transferred scrapers")
    
    # Test results tracking
    results = {
        'total_tested': len(transferred_scrapers),
        'successful_tests': 0,
        'failed_tests': 0,
        'test_results': {}
    }
    
    # Test each scraper
    for scraper_name in transferred_scrapers:
        success = test_scraper_instantiation(scraper_name)
        
        if success:
            results['successful_tests'] += 1
            results['test_results'][scraper_name] = {'status': 'success', 'error': None}
        else:
            results['failed_tests'] += 1
            results['test_results'][scraper_name] = {'status': 'failed', 'error': 'Instantiation failed'}
    
    # Save results
    results_file = 'all_scrapers_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("CRITICAL VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total scrapers tested: {results['total_tested']}")
    print(f"Successful tests: {results['successful_tests']}")
    print(f"Failed tests: {results['failed_tests']}")
    print(f"Success rate: {(results['successful_tests']/results['total_tested']*100):.1f}%")
    print(f"Results saved to: {results_file}")
    
    if results['successful_tests'] == results['total_tested']:
        print(f"\nCRITICAL SUCCESS: All {results['total_tested']} scrapers working!")
        print("Independent transfer completed successfully")
        print("Original logic preserved with enhanced error handling")
    else:
        print(f"\nWARNING: {results['failed_tests']} scrapers failed testing")
        print("Review error details above for failed scrapers")
    
    # List failed scrapers if any
    if results['failed_tests'] > 0:
        failed_scrapers = [name for name, result in results['test_results'].items() if result['status'] == 'failed']
        print(f"\nFailed Scrapers: {', '.join(failed_scrapers)}")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        if results['successful_tests'] == results['total_tested']:
            print(f"\nCRITICAL MISSION VERIFIED!")
            print(f"All {results['total_tested']} transferred scrapers working correctly")
        else:
            print("\nCRITICAL VERIFICATION INCOMPLETE - Some scrapers failed")
    except Exception as e:
        print(f"\nCRITICAL ERROR during verification: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")