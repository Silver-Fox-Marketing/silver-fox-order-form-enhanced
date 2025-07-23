#!/usr/bin/env python3
"""
Verify Thoroughbred Ford VINs are actually Ford vehicles
"""

def decode_vin_manufacturer(vin):
    """Decode VIN to identify manufacturer"""
    if len(vin) != 17:
        return "Invalid VIN length"
    
    # World Manufacturer Identifier (WMI) - first 3 characters
    wmi = vin[:3]
    
    # Common Ford WMIs
    ford_wmis = [
        '1FA', '1FB', '1FC', '1FD', '1FT', '1FM', '1FG',  # Ford USA
        '3FA', '3FB', '3FC', '3FT', '3FD', '3FM',         # Ford Mexico
        'WF0',                                            # Ford Europe
        '1FU', '1FV'                                      # Ford other
    ]
    
    # Check if it's a Ford VIN
    for ford_wmi in ford_wmis:
        if wmi.startswith(ford_wmi[:2]) or wmi == ford_wmi:
            return f"Ford (WMI: {wmi})"
    
    # Check other common manufacturers
    if wmi.startswith('1G') or wmi.startswith('3G'):
        return f"General Motors (WMI: {wmi})"
    elif wmi.startswith('4J') or wmi.startswith('WA1'):
        return f"Mercedes-Benz (WMI: {wmi})"
    elif wmi.startswith('1C') or wmi.startswith('1B'):
        return f"Chrysler/Stellantis (WMI: {wmi})"
    elif wmi.startswith('JHM') or wmi.startswith('1HG'):
        return f"Honda (WMI: {wmi})"
    else:
        return f"Other manufacturer (WMI: {wmi})"

def verify_thoroughbred_vins():
    """Verify the VINs from Thoroughbred Ford output"""
    
    print("🔍 VIN VERIFICATION: Thoroughbred Ford")
    print("Checking if scraped VINs actually match the claimed vehicles")
    print("=" * 60)
    
    # VINs from the output
    test_vins = [
        ("4JGFB4JE3NA711999", "2022 Ford (claimed)"),
        ("3GTUUDED6PG234495", "2023 Ford (claimed)"),
        ("1GC4YREY8RF106011", "2024 Ford (claimed)")  # From debug output
    ]
    
    for vin, claimed in test_vins:
        print(f"\nVIN: {vin}")
        print(f"Claimed: {claimed}")
        
        actual_make = decode_vin_manufacturer(vin)
        print(f"Actual: {actual_make}")
        
        # Check year (10th digit)
        year_codes = {
            'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015, 'G': 2016,
            'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020, 'M': 2021,
            'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025, 'T': 2026
        }
        
        year_code = vin[9]
        decoded_year = year_codes.get(year_code, f"Unknown ({year_code})")
        
        print(f"Decoded year: {decoded_year}")
        
        # Verification
        if "Ford" in actual_make and str(decoded_year) in claimed:
            print("✅ VERIFIED: VIN matches claimed vehicle")
        elif "Ford" not in actual_make:
            print(f"❌ MISMATCH: VIN is {actual_make}, not Ford!")
        else:
            print(f"⚠️ PARTIAL: Correct make but year/model issues")
        
        print("-" * 40)
    
    print(f"\n🎯 CONCLUSION:")
    print(f"This will tell us if Thoroughbred Ford is scraping accurate vehicle data")
    print(f"or if it's mixing up different vehicles/brands")

if __name__ == "__main__":
    verify_thoroughbred_vins()