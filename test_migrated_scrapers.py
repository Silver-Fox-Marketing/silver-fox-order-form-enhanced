#!/usr/bin/env python3
"""
Test migrated scrapers to ensure they work with enhanced error handling
"""

import os
import sys
import traceback
import json
from datetime import datetime

# Add bulletproof package scrapers to path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers')

def test_scraper_instantiation(scraper_name):
    """Test if a scraper can be instantiated properly"""
    
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
        
        print(f"SUCCESS: {scraper_name} instantiated successfully")
        print(f"  - Helper class: {type(scraper_instance.helper).__name__}")
        print(f"  - Data folder: {scraper_instance.data_folder}")
        print(f"  - Output file: {scraper_instance.output_file}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to instantiate {scraper_name}")
        print(f"  Error: {str(e)}")
        print(f"  Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function"""
    
    print("Testing Migrated Scrapers with Enhanced Error Handling")
    print("=" * 60)
    
    # Test a sample of migrated scrapers
    test_scrapers = [
        'BMWOFWESTSTLOUIS',
        'COLUMBIAHONDA', 
        'JOEMACHENSNISSAN',
        'AUDIRANCHOMIRAGE',
        'PAPPASTOYOTA'
    ]
    
    results = {
        'total_tested': len(test_scrapers),
        'successful_tests': 0,
        'failed_tests': 0,
        'test_results': {}
    }
    
    for scraper_name in test_scrapers:
        success = test_scraper_instantiation(scraper_name)
        
        if success:
            results['successful_tests'] += 1
            results['test_results'][scraper_name] = {'status': 'success', 'error': None}
        else:
            results['failed_tests'] += 1
            results['test_results'][scraper_name] = {'status': 'failed', 'error': 'Instantiation failed'}
    
    # Save results
    results_file = 'scraper_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Successful tests: {results['successful_tests']}")
    print(f"Failed tests: {results['failed_tests']}")
    print(f"Total tested: {results['total_tested']}")
    print(f"Results saved to: {results_file}")
    
    if results['successful_tests'] > 0:
        print(f"\nSuccessfully tested {results['successful_tests']} scrapers!")
        print("Migration appears to be working correctly with enhanced error handling")
    
    if results['failed_tests'] > 0:
        print(f"\n{results['failed_tests']} scrapers failed testing")
        print("Check error details above")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        if results['successful_tests'] > 0:
            print(f"\nTesting completed! {results['successful_tests']} scrapers working correctly.")
        else:
            print("\nTesting failed. No scrapers could be instantiated.")
    except Exception as e:
        print(f"\nCritical error during testing: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")