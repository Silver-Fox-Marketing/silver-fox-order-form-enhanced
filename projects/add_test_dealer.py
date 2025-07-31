#!/usr/bin/env python3
"""
Add Test Dealer to Database
===========================

Add the test integration dealer to the database so we can test the real scraper integration.
"""

import sys
import json
from pathlib import Path

# Add scripts directory
scripts_dir = Path(__file__).parent / "minisforum_database_transfer" / "bulletproof_package" / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from database_connection import db_manager
    
    print("Adding Test Integration Dealer to database...")
    
    # Check if it already exists
    existing = db_manager.execute_query(
        "SELECT name FROM dealership_configs WHERE name = %s",
        ("Test Integration Dealer",)
    )
    
    if existing:
        print("Test dealer already exists, updating...")
        
        db_manager.execute_query("""
            UPDATE dealership_configs 
            SET is_active = true, updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
        """, ("Test Integration Dealer",))
        
    else:
        print("Adding new test dealer...")
        
        # Add the test dealer
        db_manager.execute_query("""
            INSERT INTO dealership_configs (
                name, filtering_rules, output_rules, qr_output_path, is_active, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, (
            "Test Integration Dealer",
            json.dumps({"test": True, "integration": True}),
            json.dumps({"format": "test", "test_mode": True}),
            "test_dealer_qr/",
            True
        ))
    
    print("✅ Test Integration Dealer added successfully!")
    print()
    print("Now you can:")
    print("1. Refresh the web GUI")
    print("2. You should see 'Test Integration Dealer' in the dealerships list")
    print("3. Hit 'Run Scrape' to test the real scraper integration")
    print("4. Check the Raw Data tab for new test vehicles with timestamps")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()