#!/usr/bin/env python3
"""
Fix remaining relative imports in migrated scrapers
"""

import os
import glob
import traceback

# Configuration
SCRAPERS_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\bulletproof_package\scrapers"

def fix_file_imports(file_path):
    """Fix relative imports in a single file"""
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        changed = False
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            
            # Fix relative import patterns
            if line.strip().startswith('from . interface_class import'):
                line = 'from interface_class import *'
                changed = True
            elif line.strip().startswith('from . helper_class import'):
                line = 'from enhanced_helper_class import *'
                changed = True
            elif line.strip().startswith('from .interface_class import'):
                line = 'from interface_class import *'
                changed = True
            elif line.strip().startswith('from .helper_class import'):
                line = 'from enhanced_helper_class import *'
                changed = True
            
            fixed_lines.append(line)
        
        # Write back if changes were made
        if changed:
            fixed_content = '\n'.join(fixed_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"FIXED: {os.path.basename(file_path)}")
            return True
        else:
            print(f"OK: {os.path.basename(file_path)} (no changes needed)")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to fix {os.path.basename(file_path)}: {str(e)}")
        return False

def main():
    """Main fix function"""
    
    print("Fixing Remaining Relative Imports in Scrapers")
    print("=" * 50)
    
    # Get all Python files in scrapers directory
    scraper_files = glob.glob(os.path.join(SCRAPERS_PATH, "*.py"))
    
    # Exclude helper files
    exclude_files = ['helper_class.py', 'enhanced_helper_class.py', 'interface_class.py']
    scraper_files = [f for f in scraper_files if os.path.basename(f) not in exclude_files]
    
    print(f"Found {len(scraper_files)} scraper files to check")
    
    fixed_count = 0
    
    for file_path in sorted(scraper_files):
        if fix_file_imports(file_path):
            fixed_count += 1
    
    print("\n" + "=" * 50)
    print("IMPORT FIX SUMMARY")
    print("=" * 50)
    print(f"Files checked: {len(scraper_files)}")
    print(f"Files fixed: {fixed_count}")
    print(f"Files OK: {len(scraper_files) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\nFixed {fixed_count} files with import issues!")
    else:
        print("\nNo import issues found - all files are clean!")
    
    return fixed_count

if __name__ == "__main__":
    try:
        fixed_count = main()
        print(f"\nImport fixing completed! {fixed_count} files were updated.")
    except Exception as e:
        print(f"\nCritical error during import fixing: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")