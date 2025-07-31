#!/usr/bin/env python3
"""
Test Scraper Integration Debug
==============================

Simple test to debug why the real scrapers aren't working in the web GUI.
"""

import sys
import os
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path(__file__).parent / "minisforum_database_transfer" / "bulletproof_package" / "scripts"
sys.path.insert(0, str(scripts_dir))

print("=" * 60)
print("TESTING REAL SCRAPER INTEGRATION")
print("=" * 60)

try:
    print("1. Importing RealScraperIntegration...")
    from real_scraper_integration import RealScraperIntegration
    print("✅ Import successful!")
    
    print("\n2. Creating integration instance...")
    integration = RealScraperIntegration()
    print("✅ Instance created!")
    
    print("\n3. Testing single scraper...")
    result = integration.run_real_scraper('Columbia Honda')
    
    print("\n4. Results:")
    print(f"Success: {result.get('success', 'Unknown')}")
    print(f"Vehicle count: {result.get('vehicle_count', 0)}")
    print(f"Data source: {result.get('data_source', 'Unknown')}")
    print(f"Is real data: {result.get('is_real_data', False)}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
        
    if result.get('vehicles'):
        print(f"First vehicle sample: {result['vehicles'][0] if result['vehicles'] else 'None'}")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)