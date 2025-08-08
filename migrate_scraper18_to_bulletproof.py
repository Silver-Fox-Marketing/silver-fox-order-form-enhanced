#!/usr/bin/env python3
"""
Migrate Scraper 18 files to Bulletproof Package System
Adds enhanced error handling while preserving original scraper logic
"""

import os
import shutil
import json
import traceback
from pathlib import Path

# Configuration
SCRAPER18_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Project reference for scraper\vehicle_scraper 18\scrapers"
BULLETPROOF_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers"

# Skip files that are helper classes or old versions only
SKIP_FILES = [
    'helper_class.py',
    'interface_class.py', 
    'joemachenshyundai_old.py',  # Skip old version
    'pappastoyota_old.py'  # Skip old version
]

def get_enhanced_header():
    """Generate the enhanced header with error handling imports"""
    return """from enhanced_helper_class import *
import traceback
import sys
import os
import json
import datetime

# Database configuration for bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}
"""

def convert_scraper_content(original_content, class_name):
    """Convert original scraper content to bulletproof format"""
    
    # Remove the original import line
    lines = original_content.split('\n')
    filtered_lines = []
    
    for line in lines:
        if line.strip().startswith('from . helper_class import'):
            continue  # Skip original import
        elif line.strip() == 'self.helper = Helper()':
            # Replace with enhanced helper
            filtered_lines.append('\t\tself.helper = EnhancedHelper(DB_CONFIG)')
        else:
            filtered_lines.append(line)
    
    # Reconstruct content without original import
    converted_content = '\n'.join(filtered_lines)
    
    # Add enhanced header at the beginning
    final_content = get_enhanced_header() + '\n' + converted_content
    
    return final_content

def migrate_single_scraper(scraper_file):
    """Migrate a single scraper file with error handling"""
    
    try:
        source_path = os.path.join(SCRAPER18_PATH, scraper_file)
        dest_path = os.path.join(BULLETPROOF_PATH, scraper_file)
        
        print(f"\nMigrating {scraper_file}...")
        
        # Read original content
        with open(source_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Extract class name from filename
        class_name = scraper_file.replace('.py', '').upper()
        
        # Convert content
        converted_content = convert_scraper_content(original_content, class_name)
        
        # Write converted content
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        print(f"SUCCESS: Successfully migrated {scraper_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to migrate {scraper_file}: {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False

def main():
    """Main migration function"""
    
    print("Starting Scraper 18 to Bulletproof Package Migration")
    print("=" * 60)
    
    # Ensure bulletproof scrapers directory exists
    os.makedirs(BULLETPROOF_PATH, exist_ok=True)
    
    # Get all Python files from scraper 18
    scraper_files = [f for f in os.listdir(SCRAPER18_PATH) 
                    if f.endswith('.py') and f not in SKIP_FILES]
    
    print(f"Found {len(scraper_files)} scrapers to migrate")
    print(f"Source: {SCRAPER18_PATH}")
    print(f"Destination: {BULLETPROOF_PATH}")
    
    # Migration results tracking
    migration_results = {
        'total_scrapers': len(scraper_files),
        'successful_migrations': 0,
        'failed_migrations': 0,
        'scrapers': {}
    }
    
    # Migrate each scraper
    for scraper_file in sorted(scraper_files):
        success = migrate_single_scraper(scraper_file)
        
        if success:
            migration_results['successful_migrations'] += 1
            migration_results['scrapers'][scraper_file] = {
                'status': 'success',
                'error': None
            }
        else:
            migration_results['failed_migrations'] += 1
            migration_results['scrapers'][scraper_file] = {
                'status': 'failed',
                'error': 'Migration failed - see console output'
            }
    
    # Save results
    results_file = 'scraper18_migration_results.json'
    with open(results_file, 'w') as f:
        json.dump(migration_results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Successful migrations: {migration_results['successful_migrations']}")
    print(f"Failed migrations: {migration_results['failed_migrations']}")
    print(f"Total scrapers: {migration_results['total_scrapers']}")
    print(f"Results saved to: {results_file}")
    
    if migration_results['successful_migrations'] > 0:
        print(f"\nSuccessfully migrated {migration_results['successful_migrations']} scrapers!")
        print("All scrapers now have enhanced error handling and database integration")
    
    if migration_results['failed_migrations'] > 0:
        print(f"\n{migration_results['failed_migrations']} scrapers failed migration")
        print("   Check console output for error details")
    
    return migration_results

if __name__ == "__main__":
    try:
        results = main()
        if results['successful_migrations'] > 0:
            print(f"\nMigration completed! {results['successful_migrations']} scrapers ready for use.")
        else:
            print("\nMigration failed. No scrapers were successfully migrated.")
    except Exception as e:
        print(f"\nCritical error during migration: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")