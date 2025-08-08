#!/usr/bin/env python3
"""
Update real_scraper_integration.py to include all 40 scrapers
This will make all scrapers available in the system
"""

import os
import traceback

# Path to the real_scraper_integration.py file
INTEGRATION_FILE = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts\real_scraper_integration.py"

# All 40 scrapers mapping
ALL_SCRAPERS_MAPPING = """        # Map dealership names to their real scraper files
        self.real_scraper_mapping = {
            'Test Integration Dealer': 'test_integration_scraper.py',
            'Audi Ranch Mirage': 'audiranchomirage.py',
            'Auffenberg Hyundai': 'auffenberghyundai.py',
            'BMW of West St. Louis': 'bmwofweststlouis.py',
            'Bommarito Cadillac': 'bommaritocadillac.py',
            'Bommarito West County': 'bommaritowestcounty.py',
            'Columbia BMW': 'columbiabmw.py',
            'Columbia Honda': 'columbiahonda.py',
            'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth.py',
            'Dave Sinclair Lincoln St. Peters': 'davesinclairlincolnstpeters.py',
            'Frank Leta Honda': 'frankletahonda.py',
            'Glendale Chrysler Jeep': 'glendalechryslerjeep.py',
            'Honda of Frontenac': 'hondafrontenac.py',
            'H&W Kia': 'hwkia.py',
            'Indigo Auto Group': 'indigoautogroup.py',
            'Jaguar Ranch Mirage': 'jaguarranchomirage.py',
            'Joe Machens CDJR': 'joemachenscdjr.py',
            'Joe Machens Hyundai': 'joemachenshyundai.py',
            'Joe Machens Nissan': 'joemachensnissan.py',
            'Joe Machens Toyota': 'joemachenstoyota.py',
            'Kia of Columbia': 'kiaofcolumbia.py',
            'Land Rover Ranch Mirage': 'landroverranchomirage.py',
            'Mini of St. Louis': 'miniofstlouis.py',
            'Pappas Toyota': 'pappastoyota.py',
            'Porsche St. Louis': 'porschestlouis.py',
            'Pundmann Ford': 'pundmannford.py',
            'Rusty Drewing Cadillac': 'rustydrewingcadillac.py',
            'Rusty Drewing Chevrolet Buick GMC': 'rustydrewingchevroletbuickgmc.py',
            'Serra Honda O\\'Fallon': 'serrahondaofallon.py',
            'South County Autos': 'southcountyautos.py',
            'Spirit Lexus': 'spiritlexus.py',
            'Stehouwer Auto': 'stehouwerauto.py',
            'Suntrup Buick GMC': 'suntrupbuickgmc.py',
            'Suntrup Ford Kirkwood': 'suntrupfordkirkwood.py',
            'Suntrup Ford West': 'suntrupfordwest.py',
            'Suntrup Hyundai South': 'suntruphyundaisouth.py',
            'Suntrup Kia South': 'suntrupkiasouth.py',
            'Thoroughbred Ford': 'thoroughbredford.py',
            'Twin City Toyota': 'twincitytoyota.py',
            'West County Volvo Cars': 'wcvolvocars.py',
            'Weber Chevrolet': 'weberchev.py'
        }"""

# Expected vehicle counts mapping
VEHICLE_COUNTS_MAPPING = """        # Expected vehicle counts for progress estimation
        self.expected_vehicle_counts = {
            'Test Integration Dealer': 5,
            'Audi Ranch Mirage': 30,
            'Auffenberg Hyundai': 35,
            'BMW of West St. Louis': 55,
            'Bommarito Cadillac': 25,
            'Bommarito West County': 40,
            'Columbia BMW': 35,
            'Columbia Honda': 40,
            'Dave Sinclair Lincoln South': 25,
            'Dave Sinclair Lincoln St. Peters': 20,
            'Frank Leta Honda': 45,
            'Glendale Chrysler Jeep': 35,
            'Honda of Frontenac': 30,
            'H&W Kia': 25,
            'Indigo Auto Group': 50,
            'Jaguar Ranch Mirage': 15,
            'Joe Machens CDJR': 35,
            'Joe Machens Hyundai': 30,
            'Joe Machens Nissan': 25,
            'Joe Machens Toyota': 40,
            'Kia of Columbia': 20,
            'Land Rover Ranch Mirage': 15,
            'Mini of St. Louis': 20,
            'Pappas Toyota': 35,
            'Porsche St. Louis': 20,
            'Pundmann Ford': 30,
            'Rusty Drewing Cadillac': 25,
            'Rusty Drewing Chevrolet Buick GMC': 45,
            'Serra Honda O\\'Fallon': 35,
            'South County Autos': 25,
            'Spirit Lexus': 30,
            'Stehouwer Auto': 20,
            'Suntrup Buick GMC': 35,
            'Suntrup Ford Kirkwood': 40,
            'Suntrup Ford West': 45,
            'Suntrup Hyundai South': 30,
            'Suntrup Kia South': 25,
            'Thoroughbred Ford': 35,
            'Twin City Toyota': 30,
            'West County Volvo Cars': 25,
            'Weber Chevrolet': 40
        }"""

def update_real_scraper_integration():
    """Update the real_scraper_integration.py file"""
    
    try:
        print(f"Reading {INTEGRATION_FILE}...")
        
        # Read the current file
        with open(INTEGRATION_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the real_scraper_mapping section
        start_marker = "# Map dealership names to their real scraper files"
        end_marker = "}"
        
        # Find the start of the mapping
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("ERROR: Could not find mapping start marker")
            return False
        
        # Find the closing brace for the mapping
        brace_count = 0
        idx = content.find("{", start_idx)
        if idx == -1:
            print("ERROR: Could not find opening brace")
            return False
        
        end_idx = idx
        for i in range(idx, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        # Replace the mapping
        print("Replacing real_scraper_mapping...")
        new_content = content[:start_idx] + ALL_SCRAPERS_MAPPING + content[end_idx:]
        
        # Now update expected_vehicle_counts
        start_marker2 = "# Expected vehicle counts for progress estimation"
        start_idx2 = new_content.find(start_marker2)
        
        if start_idx2 != -1:
            # Find the closing brace for vehicle counts
            brace_count = 0
            idx = new_content.find("{", start_idx2)
            if idx != -1:
                end_idx2 = idx
                for i in range(idx, len(new_content)):
                    if new_content[i] == '{':
                        brace_count += 1
                    elif new_content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx2 = i + 1
                            break
                
                print("Replacing expected_vehicle_counts...")
                new_content = new_content[:start_idx2] + VEHICLE_COUNTS_MAPPING + new_content[end_idx2:]
        
        # Also update the scrapers path to point to bulletproof package
        old_path = 'scrapers_path = projects_root / "silverfox_scraper_system" / "silverfox_system" / "core" / "scrapers" / "dealerships"'
        new_path = 'scrapers_path = current_file.parent.parent / "scrapers"  # Point to bulletproof package scrapers'
        
        new_content = new_content.replace(old_path, new_path)
        
        # Write the updated content
        print("Writing updated file...")
        with open(INTEGRATION_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("SUCCESS: Updated real_scraper_integration.py with all 40 scrapers")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update file: {str(e)}")
        print(f"Details: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Updating Real Scraper Integration")
    print("=" * 50)
    
    if update_real_scraper_integration():
        print("\nAll 40 scrapers have been added to the real scraper mapping!")
        print("The system should now recognize all scrapers.")
        print("\nNext steps:")
        print("1. Restart the web GUI server")
        print("2. The scrapers should appear in the dropdown")
    else:
        print("\nFailed to update the integration file")