#!/usr/bin/env python3
"""
Debug Dealership Names
======================

Check what dealership names are in the database vs our scraper mapping.
"""

import sys
from pathlib import Path

# Add scripts directory
scripts_dir = Path(__file__).parent / "minisforum_database_transfer" / "bulletproof_package" / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from database_connection import db_manager
    
    print("=" * 60)
    print("CHECKING DEALERSHIP NAMES IN DATABASE")
    print("=" * 60)
    
    # Get dealership names from database
    configs = db_manager.execute_query("""
        SELECT name, is_active, updated_at
        FROM dealership_configs 
        ORDER BY name
    """)
    
    print(f"Found {len(configs)} dealerships in database:")
    print()
    
    for config in configs:
        status = "✅ ACTIVE" if config['is_active'] else "❌ INACTIVE"
        print(f"{status} | {config['name']}")
    
    print()
    print("=" * 60)
    print("REAL SCRAPER MAPPING")
    print("=" * 60)
    
    # Our real scraper mapping
    real_scraper_mapping = {
        'Columbia Honda': 'columbiahonda_real_working.py',
        'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth_real_working.py', 
        'BMW of West St. Louis': 'bmwofweststlouis_real_working.py'
    }
    
    print("Real scrapers available for:")
    for dealership in real_scraper_mapping.keys():
        print(f"🎯 {dealership}")
    
    print()
    print("=" * 60)
    print("MATCHING ANALYSIS")
    print("=" * 60)
    
    database_names = [config['name'] for config in configs]
    
    print("Checking if our real scrapers match database names:")
    for scraper_name in real_scraper_mapping.keys():
        if scraper_name in database_names:
            print(f"✅ MATCH: {scraper_name}")
        else:
            print(f"❌ NO MATCH: {scraper_name}")
            # Find closest matches
            close_matches = [name for name in database_names if any(word.lower() in name.lower() for word in scraper_name.split())]
            if close_matches:
                print(f"   Possible matches: {close_matches}")
    
    print()
    print("Checking for dealerships we could add real scrapers for:")
    potential_matches = []
    for db_name in database_names:
        if 'honda' in db_name.lower() and 'Columbia Honda' not in db_name:
            potential_matches.append(f"Honda: {db_name}")
        elif 'bmw' in db_name.lower() and 'BMW of West St. Louis' not in db_name:
            potential_matches.append(f"BMW: {db_name}")
        elif 'lincoln' in db_name.lower() and 'Dave Sinclair Lincoln South' not in db_name:
            potential_matches.append(f"Lincoln: {db_name}")
    
    if potential_matches:
        print("Potential new real scrapers:")
        for match in potential_matches:
            print(f"🔍 {match}")
    else:
        print("No obvious additional matches found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)