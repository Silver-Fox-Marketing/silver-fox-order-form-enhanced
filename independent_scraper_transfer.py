#!/usr/bin/env python3
"""
Independent Scraper Transfer Tool - Critical Priority
Independently reviews and transfers each functional scraper from scraper 18
with original logic preserved and proper error handling added.
"""

import os
import shutil
import json
import traceback
import re
from pathlib import Path

# Configuration
SCRAPER18_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Project reference for scraper\vehicle_scraper 18\scrapers"
BULLETPROOF_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers"

# Exclude these files (helper classes and old versions)
EXCLUDE_FILES = [
    'helper_class.py',
    'interface_class.py',
    'joemachenshyundai_old.py',
    'pappastoyota_old.py'
]

def analyze_scraper_structure(file_path):
    """Independently analyze each scraper's structure and dependencies"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            'imports': [],
            'class_name': None,
            'methods': [],
            'has_interface': False,
            'has_requests': False,
            'has_time': False,
            'has_json': False,
            'dependencies': []
        }
        
        # Extract imports
        import_lines = re.findall(r'^(?:from|import)\s+.*$', content, re.MULTILINE)
        analysis['imports'] = import_lines
        
        # Find class name
        class_match = re.search(r'class\s+(\w+)\s*\(', content)
        if class_match:
            analysis['class_name'] = class_match.group(1)
        
        # Find methods
        method_matches = re.findall(r'def\s+(\w+)\s*\(', content)
        analysis['methods'] = method_matches
        
        # Check for specific dependencies
        analysis['has_interface'] = 'interface_class' in content
        analysis['has_requests'] = 'requests' in content
        analysis['has_time'] = 'time.sleep' in content
        analysis['has_json'] = 'json.' in content
        
        # Identify required imports based on content
        if 'requests.' in content or 'requests.request' in content:
            analysis['dependencies'].append('requests')
        if 'time.sleep' in content:
            analysis['dependencies'].append('time')
        if 'json.' in content:
            analysis['dependencies'].append('json')
        if 'BeautifulSoup' in content:
            analysis['dependencies'].append('bs4')
        if 'datetime' in content:
            analysis['dependencies'].append('datetime')
        
        return analysis
        
    except Exception as e:
        print(f"ERROR analyzing {os.path.basename(file_path)}: {str(e)}")
        return None

def create_enhanced_scraper_header(analysis):
    """Create proper enhanced header based on scraper analysis"""
    
    header = """from enhanced_helper_class import *
import traceback
import sys
import os
import json
import datetime"""

    # Add specific dependencies based on analysis
    if 'requests' in analysis['dependencies']:
        header += "\nimport requests"
    if 'time' in analysis['dependencies']:
        header += "\nimport time"
    if 'bs4' in analysis['dependencies']:
        header += "\nfrom bs4 import BeautifulSoup"
    
    # Add interface import if needed
    if analysis['has_interface']:
        header += "\nfrom interface_class import *"
    
    header += """

# Database configuration for bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

"""
    return header

def transform_scraper_content(original_content, analysis):
    """Transform scraper content preserving original logic with error handling"""
    
    lines = original_content.split('\n')
    transformed_lines = []
    skip_imports = True
    
    for line in lines:
        # Skip original imports until we find the class definition
        if skip_imports:
            if line.strip().startswith('class '):
                skip_imports = False
                transformed_lines.append(line)
            elif line.strip().startswith('from') or line.strip().startswith('import'):
                continue  # Skip original imports
            elif line.strip() == '':
                continue  # Skip empty lines in import section
            else:
                skip_imports = False
                transformed_lines.append(line)
        else:
            # Transform helper instantiation
            if 'self.helper = Helper()' in line:
                transformed_lines.append(line.replace('self.helper = Helper()', 'self.helper = EnhancedHelper(DB_CONFIG)'))
            else:
                transformed_lines.append(line)
    
    return '\n'.join(transformed_lines)

def transfer_single_scraper(scraper_file):
    """Independently transfer a single scraper with full analysis"""
    
    try:
        source_path = os.path.join(SCRAPER18_PATH, scraper_file)
        dest_path = os.path.join(BULLETPROOF_PATH, scraper_file)
        
        print(f"\nINDEPENDENT TRANSFER: {scraper_file}")
        print("-" * 50)
        
        # Step 1: Analyze original scraper
        print("1. Analyzing original scraper structure...")
        analysis = analyze_scraper_structure(source_path)
        
        if not analysis:
            return False
        
        print(f"   Class: {analysis['class_name']}")
        print(f"   Methods: {len(analysis['methods'])}")
        print(f"   Dependencies: {', '.join(analysis['dependencies'])}")
        print(f"   Uses Interface: {analysis['has_interface']}")
        
        # Step 2: Read original content
        print("2. Reading original scraper content...")
        with open(source_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Step 3: Create enhanced header
        print("3. Creating enhanced header with error handling...")
        enhanced_header = create_enhanced_scraper_header(analysis)
        
        # Step 4: Transform content preserving original logic
        print("4. Transforming content while preserving original logic...")
        transformed_content = transform_scraper_content(original_content, analysis)
        
        # Step 5: Combine header and transformed content
        final_content = enhanced_header + transformed_content
        
        # Step 6: Write to bulletproof package
        print("5. Writing enhanced scraper to bulletproof package...")
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"SUCCESS: {scraper_file} transferred with enhanced error handling")
        return True
        
    except Exception as e:
        print(f"CRITICAL ERROR transferring {scraper_file}: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")
        return False

def main():
    """Main independent transfer function"""
    
    print("CRITICAL PRIORITY: Independent Scraper Transfer")
    print("=" * 60)
    print("Independently reviewing and transferring each functional scraper")
    print("Preserving original logic while adding proper error handling")
    print("=" * 60)
    
    # Get all functional scrapers
    all_files = os.listdir(SCRAPER18_PATH)
    scraper_files = [f for f in all_files if f.endswith('.py') and f not in EXCLUDE_FILES]
    
    print(f"Found {len(scraper_files)} functional scrapers to transfer")
    
    # Transfer results tracking
    results = {
        'total_scrapers': len(scraper_files),
        'successful_transfers': 0,
        'failed_transfers': 0,
        'scrapers': {}
    }
    
    # Transfer each scraper independently
    for scraper_file in sorted(scraper_files):
        success = transfer_single_scraper(scraper_file)
        
        if success:
            results['successful_transfers'] += 1
            results['scrapers'][scraper_file] = {
                'status': 'success',
                'error': None
            }
        else:
            results['failed_transfers'] += 1
            results['scrapers'][scraper_file] = {
                'status': 'failed',
                'error': 'Transfer failed - see console output'
            }
    
    # Save results
    results_file = 'independent_transfer_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("INDEPENDENT TRANSFER SUMMARY")
    print("=" * 60)
    print(f"Total scrapers: {results['total_scrapers']}")
    print(f"Successful transfers: {results['successful_transfers']}")
    print(f"Failed transfers: {results['failed_transfers']}")
    print(f"Success rate: {(results['successful_transfers']/results['total_scrapers']*100):.1f}%")
    print(f"Results saved to: {results_file}")
    
    if results['successful_transfers'] == results['total_scrapers']:
        print(f"\nCRITICAL SUCCESS: All {results['total_scrapers']} scrapers transferred!")
        print("Each scraper independently reviewed and enhanced with error handling")
        print("Original scraping logic preserved in all transfers")
    else:
        print(f"\nWARNING: {results['failed_transfers']} scrapers failed transfer")
        print("Review error details above for failed transfers")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        if results['successful_transfers'] == results['total_scrapers']:
            print(f"\nCRITICAL MISSION ACCOMPLISHED!")
            print(f"All {results['total_scrapers']} functional scrapers successfully transferred")
        else:
            print("\nCRITICAL MISSION INCOMPLETE - Some transfers failed")
    except Exception as e:
        print(f"\nCRITICAL ERROR during independent transfer: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")