#!/usr/bin/env python3
"""
Fix Suntrup Ford West pricing extraction
The current _safe_int method is too aggressive and breaks price parsing
"""

def fix_suntrup_ford_west_pricing():
    """Fix the broken price extraction in Suntrup Ford West scraper"""
    
    print("🔧 FIXING: Suntrup Ford West Price Extraction")
    print("Current issue: $500-$4K prices for 2025 Broncos (should be $30K+)")
    print("=" * 60)
    
    scraper_path = '/Users/barretttaylor/Desktop/Claude Code/silverfox_assistant/scraper/dealerships/suntrupfordwest_working.py'
    
    try:
        with open(scraper_path, 'r') as f:
            content = f.read()
        
        # Find the broken _safe_int method
        old_safe_int = '''    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas or dollar signs
            if isinstance(value, str):
                value = re.sub(r'[^\\d]', '', value)
            return int(float(str(value))) if value else None
        except (ValueError, TypeError):
            return None'''
        
        # Replace with improved price parsing
        new_safe_int = '''    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer with proper price handling"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas or dollar signs
            if isinstance(value, str):
                # Remove $ and commas but preserve decimal points
                cleaned = re.sub(r'[$,]', '', value.strip())
                # Handle decimal prices (convert to cents then back to dollars)
                if '.' in cleaned:
                    return int(float(cleaned))
                else:
                    return int(cleaned) if cleaned.isdigit() else None
            return int(float(str(value))) if value else None
        except (ValueError, TypeError):
            return None'''
        
        if old_safe_int.replace('\\', '') in content:
            content = content.replace(old_safe_int.replace('\\', ''), new_safe_int)
            print("✅ Updated _safe_int method with proper price handling")
        else:
            print("❌ Could not find _safe_int method to fix")
            return False
        
        # Also improve the Chrome price extraction regex
        old_chrome_price = '''            # Extract price ($XX,XXX pattern)
            price_match = re.search(r'\\$[\\d,]+', text)
            if price_match:
                price_str = price_match.group().replace('$', '').replace(',', '')
                try:
                    vehicle['price'] = int(price_str)
                except ValueError:
                    pass'''
        
        new_chrome_price = '''            # Extract price (improved pattern for $XX,XXX)
            price_patterns = [
                r'\\$([\\d,]+\\.?\\d*)',  # $30,000 or $30,000.00
                r'Price[:\\s]+\\$([\\d,]+)',  # Price: $30,000
                r'MSRP[:\\s]+\\$([\\d,]+)',   # MSRP: $30,000
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, text, re.IGNORECASE)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    try:
                        vehicle['price'] = int(float(price_str))
                        break
                    except ValueError:
                        continue'''
        
        if old_chrome_price.replace('\\', '') in content:
            content = content.replace(old_chrome_price.replace('\\', ''), new_chrome_price)
            print("✅ Improved Chrome price extraction with better patterns")
        else:
            print("⚠️ Could not find Chrome price extraction to improve")
        
        # Write the fixed scraper
        with open(scraper_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed scraper saved")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_fixed_pricing():
    """Test the fixed pricing extraction"""
    
    print(f"\n🧪 TESTING FIXED PRICING:")
    print("Verifying price extraction now works correctly")
    print("-" * 40)
    
    try:
        import sys
        import os
        sys.path.append('scraper')
        
        import importlib
        importlib.invalidate_caches()
        
        module = importlib.import_module('dealerships.suntrupfordwest_working')
        importlib.reload(module)
        
        # Get scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                hasattr(obj, 'scrape_inventory')):
                scraper_class = obj
                break
        
        if not scraper_class:
            print("❌ No scraper class found")
            return False
        
        config = {
            'name': 'Suntrup Ford West',
            'base_url': 'https://www.suntrupfordwest.com'
        }
        
        scraper = scraper_class(config)
        
        # Test the improved _safe_int method
        if hasattr(scraper, '_safe_int'):
            print("✅ _safe_int method exists")
            
            # Test with price values
            test_prices = {
                '30000': 30000,
                '$30,000': 30000,
                '$30,000.00': 30000,
                '45500': 45500,
                '$45,500': 45500,
                '500': 500,  # This should still work for legitimate $500 prices
            }
            
            for input_val, expected in test_prices.items():
                result = scraper._safe_int(input_val)
                status = "✅" if result == expected else "❌"
                print(f"   {status} '{input_val}' → {result} (expected {expected})")
        
        print("\n📊 Testing full scraper with fixed pricing...")
        vehicles = scraper.scrape_inventory()
        
        if vehicles:
            price_issues = []
            realistic_prices = []
            
            for vehicle in vehicles:
                price = vehicle.get('price')
                year = vehicle.get('year')
                model = vehicle.get('model', '')
                
                if price:
                    if price >= 15000:  # Realistic minimum
                        realistic_prices.append((price, year, model))
                    else:
                        price_issues.append((price, year, model))
            
            print(f"   ✅ Realistic prices: {len(realistic_prices)}")
            print(f"   ❌ Unrealistic prices: {len(price_issues)}")
            
            if realistic_prices:
                print(f"\n   📋 Sample realistic prices:")
                for price, year, model in realistic_prices[:3]:
                    print(f"      ${price:,} - {year} {model}")
            
            if price_issues:
                print(f"\n   ⚠️ Price issues found:")
                for price, year, model in price_issues[:3]:
                    print(f"      ${price} - {year} {model} (too low)")
            
            success_rate = len(realistic_prices) / len(vehicles) * 100 if vehicles else 0
            
            if success_rate >= 80:
                print(f"\n   🎯 SUCCESS: {success_rate:.1f}% of prices are now realistic!")
                return True
            else:
                print(f"\n   ⚠️ PARTIAL: {success_rate:.1f}% realistic prices (need >80%)")
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
    print("🔧 SUNTRUP FORD WEST PRICING FIX")
    print("=" * 60)
    
    # Fix the pricing
    fix_success = fix_suntrup_ford_west_pricing()
    
    if fix_success:
        # Test the fix
        test_success = test_fixed_pricing()
        
        if test_success:
            print(f"\n🎯 SUCCESS: Suntrup Ford West pricing fixed!")
            print(f"   ✅ Prices now realistic for 2025 vehicles")
            print(f"   ✅ Improved price extraction patterns")
            print(f"   📋 Ready for accurate on-lot methodology application")
        else:
            print(f"\n⚠️ Fix applied but prices still need work")
    else:
        print(f"\n❌ Could not apply pricing fix")