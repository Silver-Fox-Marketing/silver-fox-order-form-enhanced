#!/usr/bin/env python3
"""
Manual Joe Machens Nissan Website Verification
Direct inspection of their website to verify actual inventory count
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def manual_website_verification():
    """Manually verify Joe Machens Nissan website like a human would"""
    print("🔍 MANUAL VERIFICATION: Joe Machens Nissan Website")
    print("Checking the website exactly like a human customer would")
    print("=" * 70)
    
    # Use non-headless mode to see what's actually happening
    options = Options()
    # Remove headless to see the actual website
    # options.add_argument('--headless')  # Comment out to see browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Step 1: Visit homepage like a customer
        print("📡 Step 1: Visiting Joe Machens Nissan homepage")
        driver.get("https://www.joemachensnissan.com")
        time.sleep(3)
        
        print("   ✅ Homepage loaded")
        print(f"   Page title: {driver.title}")
        
        # Step 2: Look for inventory navigation
        print("\n🔍 Step 2: Looking for inventory navigation options")
        
        # Find navigation links
        nav_links = driver.find_elements(By.TAG_NAME, 'a')
        inventory_links = []
        
        for link in nav_links:
            try:
                text = link.text.strip().lower()
                href = link.get_attribute('href') or ''
                
                if any(keyword in text for keyword in ['inventory', 'vehicles', 'cars', 'search', 'browse']):
                    inventory_links.append({
                        'text': link.text.strip(),
                        'href': href,
                        'visible': link.is_displayed()
                    })
            except:
                continue
        
        print(f"   Found {len(inventory_links)} potential inventory links:")
        for i, link in enumerate(inventory_links[:10]):
            status = "✅ Visible" if link['visible'] else "❌ Hidden"
            print(f"      {i+1}. '{link['text']}' -> {link['href'][:60]}... ({status})")
        
        # Step 3: Try the main inventory page
        print("\n📡 Step 3: Checking main inventory page")
        inventory_url = "https://www.joemachensnissan.com/inventory"
        driver.get(inventory_url)
        time.sleep(5)  # Give it time to load
        
        # Check what's actually on the page
        print("   ✅ Inventory page loaded")
        
        # Look for vehicles
        vehicle_elements = driver.find_elements(By.CSS_SELECTOR, '[data-vehicle]')
        print(f"   📊 Found {len(vehicle_elements)} vehicles with [data-vehicle] selector")
        
        # Try other selectors
        other_selectors = ['.vehicle-card', '.inventory-item', '.vehicle-tile']
        for selector in other_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   📊 Found {len(elements)} vehicles with {selector} selector")
            except:
                continue
        
        # Step 4: Look for pagination or load more
        print("\n🔍 Step 4: Checking for pagination or load more options")
        
        # Check for pagination elements
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, '.pagination, .pager, [data-page]')
        if pagination_elements:
            print(f"   ✅ Found {len(pagination_elements)} pagination elements")
            for i, elem in enumerate(pagination_elements):
                try:
                    print(f"      Pagination {i+1}: {elem.text.strip()}")
                except:
                    print(f"      Pagination {i+1}: [No text]")
        else:
            print("   ❌ No pagination elements found")
        
        # Check for load more buttons
        load_more_candidates = driver.find_elements(By.XPATH, "//*[contains(text(), 'more') or contains(text(), 'More') or contains(text(), 'load') or contains(text(), 'Load')]")
        if load_more_candidates:
            print(f"   ✅ Found {len(load_more_candidates)} potential load more elements")
            for i, elem in enumerate(load_more_candidates[:5]):
                try:
                    text = elem.text.strip()
                    tag = elem.tag_name
                    visible = elem.is_displayed()
                    print(f"      Load More {i+1}: <{tag}> '{text}' (Visible: {visible})")
                except:
                    print(f"      Load More {i+1}: [Error reading element]")
        else:
            print("   ❌ No load more elements found")
        
        # Step 5: Check page source for hidden inventory counts
        print("\n🔍 Step 5: Analyzing page source for inventory indicators")
        
        page_source = driver.page_source.lower()
        
        # Look for common inventory count patterns
        count_patterns = [
            (r'(\d+)\s+(?:vehicles?|cars?|results?)', 'vehicles/cars/results'),
            (r'(?:showing|found|total):\s*(\d+)', 'showing/found/total'),
            (r'(\d+)\s+(?:of|total)', 'of/total'),
            (r'(\d+)\s+nissan', 'nissan mentions'),
            (r'inventory["\']?[>:]\s*(\d+)', 'inventory counts')
        ]
        
        found_any_counts = False
        for pattern, description in count_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                found_any_counts = True
                counts = []
                for match in matches:
                    try:
                        count = int(match)
                        if 1 <= count <= 2000:  # Reasonable range
                            counts.append(count)
                    except:
                        continue
                
                if counts:
                    unique_counts = sorted(set(counts), reverse=True)
                    print(f"   📊 {description}: {unique_counts[:10]}")
        
        if not found_any_counts:
            print("   ❌ No inventory count patterns found in page source")
        
        # Step 6: Try different inventory access methods
        print("\n🔍 Step 6: Trying alternative inventory access methods")
        
        alternative_urls = [
            "https://www.joemachensnissan.com/new-inventory",
            "https://www.joemachensnissan.com/used-inventory", 
            "https://www.joemachensnissan.com/inventory/new",
            "https://www.joemachensnissan.com/inventory/used",
            "https://www.joemachensnissan.com/inventory/certified",
            "https://www.joemachensnissan.com/search",
            "https://www.joemachensnissan.com/vehicles/new",
            "https://www.joemachensnissan.com/vehicles/used"
        ]
        
        for url in alternative_urls:
            try:
                print(f"   📡 Trying: {url}")
                driver.get(url)
                time.sleep(2)
                
                # Quick vehicle count
                vehicles = driver.find_elements(By.CSS_SELECTOR, '[data-vehicle], .vehicle-card, .inventory-item')
                status_code = "✅ Accessible" if "404" not in driver.page_source and "error" not in driver.page_source.lower() else "❌ Not found"
                
                print(f"      {status_code}, {len(vehicles)} vehicles found")
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:30]}")
        
        # Step 7: Final assessment
        print("\n📋 MANUAL VERIFICATION RESULTS")
        print("=" * 50)
        
        # Go back to main inventory page for final count
        driver.get("https://www.joemachensnissan.com/inventory")
        time.sleep(5)
        
        final_vehicle_count = len(driver.find_elements(By.CSS_SELECTOR, '[data-vehicle]'))
        
        print(f"Final vehicle count on main inventory page: {final_vehicle_count}")
        print(f"Page URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Let user see the page
        print(f"\n👀 BROWSER WINDOW OPEN FOR MANUAL INSPECTION")
        print(f"The browser window is now open showing Joe Machens Nissan inventory.")
        print(f"Please manually verify:")
        print(f"   1. How many vehicles do you see on the page?")
        print(f"   2. Are there pagination controls visible?") 
        print(f"   3. Are there load more buttons?")
        print(f"   4. Does the count match our scraper result of 20?")
        
        input("\nPress Enter after you've manually verified the website...")
        
        return {
            'scraped_count': final_vehicle_count,
            'has_pagination': len(pagination_elements) > 0,
            'has_load_more': len(load_more_candidates) > 0,
            'page_accessible': True
        }
        
    except Exception as e:
        print(f"❌ Manual verification failed: {str(e)}")
        return {'error': str(e)}
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    print("🎯 MANUAL WEBSITE VERIFICATION")
    print("This will open a browser window for manual inspection")
    print()
    
    result = manual_website_verification()
    
    if 'error' not in result:
        print(f"\n✅ Manual verification complete!")
        print(f"Please confirm if our scraper result of 20 vehicles matches what you saw manually.")
    else:
        print(f"\n❌ Verification failed: {result['error']}")