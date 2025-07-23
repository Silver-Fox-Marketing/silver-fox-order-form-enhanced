#!/usr/bin/env python3
"""
Fix Thoroughbred Ford VIN extraction by filtering out non-Ford VINs
"""

def fix_thoroughbred_ford_vins():
    """Add Ford VIN validation to Thoroughbred Ford scraper"""
    
    print("🔧 FIXING: Thoroughbred Ford VIN Validation")
    print("Adding Ford-specific VIN filtering to remove Mercedes/GM contamination")
    print("=" * 60)
    
    # Read the current scraper
    scraper_path = '/Users/barretttaylor/Desktop/Claude Code/silverfox_assistant/scraper/dealerships/thoroughbredford_onlot_integrated.py'
    
    try:
        with open(scraper_path, 'r') as f:
            content = f.read()
        
        # Find the VIN extraction section
        if "vin_match = re.search(r'VIN[:\\s]+([A-HJ-NPR-Z0-9]{17})', text_content.upper())" in content:
            print("✅ Found VIN extraction regex")
            
            # Add Ford VIN validation method
            ford_vin_validator = '''
    def _is_ford_vin(self, vin: str) -> bool:
        """Validate that VIN belongs to Ford Motor Company"""
        if not vin or len(vin) != 17:
            return False
        
        # Ford World Manufacturer Identifiers (WMI)
        ford_wmis = [
            '1FA', '1FB', '1FC', '1FD', '1FT', '1FM', '1FG',  # Ford USA
            '3FA', '3FB', '3FC', '3FT', '3FD', '3FM',         # Ford Mexico  
            'WF0',                                            # Ford Europe
            '1FU', '1FV'                                      # Ford other
        ]
        
        wmi = vin[:3]
        
        # Check exact match or prefix match for Ford WMIs
        for ford_wmi in ford_wmis:
            if wmi == ford_wmi or wmi.startswith(ford_wmi[:2]):
                return True
        
        return False'''
            
            # Insert the method before the scrape_inventory method
            if "def scrape_inventory(self) -> List[Dict[str, Any]]:" in content:
                insertion_point = content.find("def scrape_inventory(self) -> List[Dict[str, Any]]:")
                content = content[:insertion_point] + ford_vin_validator + "\n\n    " + content[insertion_point:]
                print("✅ Added Ford VIN validation method")
            
            # Update the VIN extraction to validate Ford VINs
            old_vin_extraction = '''                    # Look for VIN
                    vin_match = re.search(r'VIN[:\\s]+([A-HJ-NPR-Z0-9]{17})', text_content.upper())
                    if vin_match:
                        vehicle['vin'] = vin_match.group(1)'''
            
            new_vin_extraction = '''                    # Look for VIN (Ford only)
                    vin_match = re.search(r'VIN[:\\s]+([A-HJ-NPR-Z0-9]{17})', text_content.upper())
                    if vin_match:
                        potential_vin = vin_match.group(1)
                        if self._is_ford_vin(potential_vin):
                            vehicle['vin'] = potential_vin
                        else:
                            self.logger.debug(f"Filtered out non-Ford VIN: {potential_vin[:8]}...")'''
            
            content = content.replace(old_vin_extraction, new_vin_extraction)
            print("✅ Updated VIN extraction with Ford validation")
            
            # Also add validation to API data extraction
            if "vehicle['vin'] = raw_vehicle.get('vin') or raw_vehicle.get('VIN')" in content:
                old_api_vin = "vehicle['vin'] = raw_vehicle.get('vin') or raw_vehicle.get('VIN')"
                new_api_vin = '''potential_vin = raw_vehicle.get('vin') or raw_vehicle.get('VIN')
            if potential_vin and self._is_ford_vin(potential_vin):
                vehicle['vin'] = potential_vin
            else:
                vehicle['vin'] = None  # Filter out non-Ford VINs'''
                
                content = content.replace(old_api_vin, new_api_vin)
                print("✅ Updated API VIN extraction with Ford validation")
            
            # Write the fixed scraper
            with open(scraper_path, 'w') as f:
                f.write(content)
            
            print("✅ Fixed scraper saved")
            return True
            
        else:
            print("❌ Could not find VIN extraction regex to fix")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing scraper: {str(e)}")
        return False

def test_fixed_scraper():
    """Test the fixed scraper"""
    
    print(f"\n🧪 TESTING FIXED SCRAPER:")
    print("Verifying Ford VIN validation works")
    print("-" * 40)
    
    try:
        import sys
        import os
        sys.path.append('scraper')
        
        import importlib
        importlib.invalidate_caches()  # Clear import cache
        
        module = importlib.import_module('dealerships.thoroughbredford_onlot_integrated')
        importlib.reload(module)  # Reload with changes
        
        # Get scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                hasattr(obj, 'scrape_inventory') and 
                'ThoroughbredFord' in name):
                scraper_class = obj
                break
        
        if not scraper_class:
            print("❌ No scraper class found")
            return False
        
        config = {
            'name': 'Thoroughbred Ford',
            'base_url': 'https://www.thoroughbredford.com'
        }
        
        scraper = scraper_class(config)
        
        # Test the VIN validation method
        if hasattr(scraper, '_is_ford_vin'):
            print("✅ Ford VIN validation method exists")
            
            # Test with known VINs
            test_vins = {
                '1FAGP8FF4R5108339': True,   # Ford (1FA)
                '4JGFB4JE3NA711999': False,  # Mercedes (4JG)
                '3GTUUDED6PG234495': False,  # GM (3GT)
                '1FT8W2BM3REC05809': True,   # Ford (1FT)
            }
            
            for vin, expected in test_vins.items():
                result = scraper._is_ford_vin(vin)
                status = "✅" if result == expected else "❌"
                print(f"   {status} VIN {vin[:8]}: {result} (expected {expected})")
        
        else:
            print("❌ Ford VIN validation method not found")
            return False
        
        print("\n📊 Testing full scraper with Ford VIN filtering...")
        vehicles = scraper.scrape_inventory()
        
        if vehicles:
            ford_vins = 0
            non_ford_vins = 0
            
            for vehicle in vehicles:
                vin = vehicle.get('vin')
                if vin:
                    if scraper._is_ford_vin(vin):
                        ford_vins += 1
                    else:
                        non_ford_vins += 1
            
            print(f"   ✅ Ford VINs: {ford_vins}")
            print(f"   ❌ Non-Ford VINs: {non_ford_vins}")
            
            if non_ford_vins == 0:
                print(f"   🎯 SUCCESS: All VINs are now Ford vehicles!")
                return True
            else:
                print(f"   ⚠️ Still found {non_ford_vins} non-Ford VINs")
                return False
        else:
            print("   ❌ No vehicles returned")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 THOROUGHBRED FORD VIN VALIDATION FIX")
    print("=" * 60)
    
    # Fix the scraper
    fix_success = fix_thoroughbred_ford_vins()
    
    if fix_success:
        # Test the fix
        test_success = test_fixed_scraper()
        
        if test_success:
            print(f"\n🎯 SUCCESS: Thoroughbred Ford VIN contamination fixed!")
            print(f"   ✅ Only Ford VINs will now be extracted")
            print(f"   ✅ Mercedes/GM VINs filtered out")
            print(f"   📋 Ready for accurate on-lot methodology application")
        else:
            print(f"\n⚠️ Fix applied but testing showed issues")
    else:
        print(f"\n❌ Could not apply fix")