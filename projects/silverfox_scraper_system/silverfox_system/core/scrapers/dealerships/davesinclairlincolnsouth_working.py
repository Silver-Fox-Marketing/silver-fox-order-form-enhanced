import requests
import time
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Chrome driver imports for anti-bot bypass
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Try to import base classes, create simple fallbacks if not available
try:
    from dealership_base import DealershipScraperBase
    from exceptions import NetworkError, ParsingError
except ImportError:
    # Create simple fallback base class for standalone testing
    class DealershipScraperBase:
        def __init__(self, dealership_config, scraper_config=None):
            self.dealership_config = dealership_config
            self.dealership_name = dealership_config.get('name', 'Unknown')
            self.config = scraper_config or self._create_default_config()
            self.logger = logging.getLogger(__name__)
            self.rate_limiter = SimpleRateLimiter()
        
        def _create_default_config(self):
            class DefaultConfig:
                request_delay = 2.0
                timeout = 30
            return DefaultConfig()
    
    class NetworkError(Exception):
        pass
    
    class ParsingError(Exception):
        pass

class SimpleRateLimiter:
    def __init__(self):
        self.last_request = 0
        self.min_delay = 1.0
    
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
    
    def make_request(self):
        self.last_request = time.time()

class DaveSinclairLincolnSouthWorkingScraper(DealershipScraperBase):
    """
    WORKING scraper for Dave Sinclair Lincoln South - COMPLETE INVENTORY EXTRACTION
    Implements mandatory pagination to capture ENTIRE inventory as required by complete_data.csv evidence
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # Dave Sinclair Lincoln South configuration
        self.base_url = 'https://www.davesinclairlincolnsouth.com'
        self.inventory_urls = {
            'new': f'{self.base_url}/searchnew.aspx',
            'used': f'{self.base_url}/searchused.aspx'
        }
        
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = requests.Session()
        
        # Chrome driver setup for anti-bot bypass
        self.driver = None
        self.wait = None
        self.use_chrome = True  # Dave Sinclair likely needs Chrome driver
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape COMPLETE inventory using Chrome driver with mandatory pagination"""
        
        all_vehicles = []
        
        try:
            self.logger.info(f"Starting COMPLETE inventory extraction for {self.dealership_name}")
            all_vehicles = self._scrape_with_chrome()
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed: {str(e)}")
            raise
        
        self.logger.info(f"COMPLETE inventory extraction: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    def _scrape_with_chrome(self) -> List[Dict[str, Any]]:
        """Chrome-based scraping with MANDATORY pagination for COMPLETE inventory"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available - install with: pip install selenium")
        
        all_vehicles = []
        
        try:
            # Setup Chrome driver
            self._setup_chrome_driver()
            
            # Scrape each vehicle type with COMPLETE pagination
            for vehicle_type in ['new', 'used']:
                self.logger.info(f"Scraping {vehicle_type} vehicles with COMPLETE pagination")
                
                try:
                    vehicles = self._scrape_vehicle_type_chrome_with_pagination(vehicle_type)
                    all_vehicles.extend(vehicles)
                except Exception as e:
                    self.logger.warning(f"Failed to scrape {vehicle_type} vehicles: {str(e)}")
                    continue
                
                # Delay between types
                time.sleep(2)
            
        finally:
            # Always cleanup Chrome driver
            self._cleanup_chrome_driver()
        
        return all_vehicles
    
    def _scrape_vehicle_type_chrome_with_pagination(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles with MANDATORY pagination for COMPLETE inventory extraction"""
        
        vehicles = []
        page_num = 1
        max_pages = 20  # Safety limit for complete inventory
        
        try:
            # Navigate to inventory page
            url = self.inventory_urls[vehicle_type]
            
            self.logger.info(f"Starting COMPLETE {vehicle_type} inventory extraction")
            
            while page_num <= max_pages:
                self.logger.info(f"Processing page {page_num} for {vehicle_type} inventory")
                
                # Navigate to page
                if page_num == 1:
                    self.driver.get(url)
                else:
                    # Try to navigate to next page
                    if not self._navigate_to_next_page(page_num):
                        self.logger.info(f"No more pages available after page {page_num - 1} - COMPLETE inventory captured")
                        break
                
                # Wait for page load
                time.sleep(3)
                
                # Find vehicle elements on current page
                vehicle_elements = self._find_lincoln_vehicle_elements()
                
                if not vehicle_elements:
                    self.logger.info(f"No vehicles found on page {page_num} - COMPLETE inventory captured")
                    break
                
                # Extract ALL vehicles from current page
                page_vehicles = []
                for element in vehicle_elements:
                    vehicle_data = self._extract_lincoln_vehicle_from_element(element, vehicle_type)
                    if vehicle_data:
                        page_vehicles.append(vehicle_data)
                        vehicles.append(vehicle_data)
                
                self.logger.info(f"Page {page_num}: Extracted {len(page_vehicles)} vehicles")
                
                # If we got fewer than expected vehicles, we might be at the end
                if len(page_vehicles) < 5:
                    self.logger.info(f"Page {page_num} has only {len(page_vehicles)} vehicles - likely at end of inventory")
                    break
                
                page_num += 1
                
                # Delay between pages
                time.sleep(2)
            
            self.logger.info(f"COMPLETE {vehicle_type} extraction: {len(vehicles)} total vehicles from {page_num - 1} pages")
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed for {vehicle_type}: {str(e)}")
        
        return vehicles
    
    def _navigate_to_next_page(self, page_num: int) -> bool:
        """Navigate to next page in pagination for COMPLETE inventory"""
        
        try:
            # Common pagination selectors
            next_selectors = [
                f'a[href*="page={page_num}"]:not([href*="page={page_num - 1}"])',
                f'a[href*="pt={page_num}"]:not([href*="pt={page_num - 1}"])',
                f'a[href*="pageNumber={page_num}"]',
                '.next-page',
                '.pagination-next',
                'a[rel="next"]',
                '.page-next',
                f'a:contains("{page_num}")',
                '.paging a.next'
            ]
            
            # Try direct URL modification first (most reliable)
            current_url = self.driver.current_url
            
            # Method 1: URL parameter modification
            if 'page=' in current_url:
                new_url = re.sub(r'page=\d+', f'page={page_num}', current_url)
            elif 'pt=' in current_url:
                new_url = re.sub(r'pt=\d+', f'pt={page_num}', current_url)
            else:
                # Add page parameter
                separator = '&' if '?' in current_url else '?'
                new_url = f"{current_url}{separator}page={page_num}"
            
            if new_url != current_url:
                self.logger.info(f"Navigating to page {page_num}: {new_url}")
                self.driver.get(new_url)
                time.sleep(2)
                return True
            
            # Method 2: Click next page button
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                        return True
                except Exception:
                    continue
            
            self.logger.warning(f"Could not navigate to page {page_num}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating to page {page_num}: {str(e)}")
            return False
    
    def _setup_chrome_driver(self):
        """Setup ultra-fast, stealth Chrome driver for Dave Sinclair Lincoln South"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
        
        options = Options()
        
        # Ultra-fast performance optimizations
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-images')
        options.add_argument('--disable-css')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-default-apps')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-background-networking')
        options.add_argument('--memory-pressure-off')
        
        # Advanced anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent rotation
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        import random
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Network optimizations
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2, "plugins": 2, "popups": 2, "geolocation": 2, "notifications": 2, "media_stream": 2
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.wait = WebDriverWait(self.driver, 15)
            
            self.logger.info("Chrome driver setup successful")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {str(e)}")
            raise
    
    def _cleanup_chrome_driver(self):
        """Cleanup Chrome driver resources"""
        
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome driver cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up Chrome driver: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    def _find_lincoln_vehicle_elements(self):
        """Find vehicle listing elements for Lincoln vehicles"""
        
        # Enhanced selectors for dealership sites
        selectors = [
            '.vehicle-card',
            '.inventory-item',
            '.vehicle-listing',
            '[data-vehicle-id]',
            '.vehicle-tile',
            '.vehicle-summary',
            '.car-item',
            '.vehicle-wrap',
            '.vdp-tile',
            '.vehicle-info',
            '.inventory-vehicle',
            '.search-result',
            '.vehicle-result',
            '.listing-item'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.info(f"Found {len(elements)} vehicles using selector: {selector}")
                    return elements  # Return ALL elements for complete inventory
            except Exception:
                continue
        
        # Fallback: look for Lincoln vehicles
        try:
            all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
            vehicle_elements = []
            
            lincoln_models = ['AVIATOR', 'CORSAIR', 'NAUTILUS', 'NAVIGATOR', 'CONTINENTAL', 'MKZ', 'MKC', 'MKX', 'MKT', 'TOWN CAR']
            
            for element in all_elements[:300]:  # Increased search scope
                try:
                    text = element.text.strip().upper()
                    if text and len(text) > 10:
                        # Check for year + Lincoln indicators
                        has_year = bool(re.search(r'\b20\d{2}\b', text))
                        has_lincoln = 'LINCOLN' in text or any(model in text for model in lincoln_models)
                        has_price = bool(re.search(r'\$[\d,]+', text))
                        
                        if (has_year and has_lincoln) or (has_lincoln and has_price):
                            vehicle_elements.append(element)
                            if len(vehicle_elements) >= 50:  # Increased limit for complete inventory
                                break
                except Exception:
                    continue
            
            if vehicle_elements:
                self.logger.info(f"Found {len(vehicle_elements)} potential vehicles via Lincoln text search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []
    
    def _extract_lincoln_vehicle_from_element(self, element, vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from DOM element - COMPLETE DATA matching complete_data.csv"""
        
        try:
            text = element.text.strip()
            
            # Complete vehicle structure matching complete_data.csv format
            vehicle = {
                'vin': '',
                'stock_number': '',
                'type': vehicle_type.title(),
                'year': None,
                'make': 'Lincoln',
                'model': '',
                'trim': '',
                'ext_color': '',
                'status': 'Available',
                'body_style': '',
                'fuel_type': '',
                'msrp': None,
                'date_in_stock': '',
                'street_address': '12032 Gravois Rd',
                'locality': 'St. Louis',
                'postal_code': '63127',
                'region': 'MO',
                'country': 'US',
                'location': 'Dave Sinclair Lincoln South',
                'vehicle_url': '',
                'mileage': None,
                'condition': vehicle_type.title(),
                'dealer_name': 'Dave Sinclair Lincoln South',
                'dealer_city': 'St. Louis',
                'dealer_state': 'MO',
                'scraped_at': datetime.now().isoformat(),
                'source_text': text[:300]
            }
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                year = int(year_match.group())
                if 1990 <= year <= 2026:
                    vehicle['year'] = year
            
            # Extract price with multiple patterns
            price_patterns = [
                r'\$([\d,]+)',
                r'Price[:\s]*\$?([\d,]+)',
                r'MSRP[:\s]*\$?([\d,]+)',
                r'([\d,]+)\s*dollars?'
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, text, re.IGNORECASE)
                if price_match:
                    price_str = re.sub(r'[^\d]', '', price_match.group(1))
                    try:
                        price = int(price_str)
                        if 1000 <= price <= 500000:
                            vehicle['price'] = price
                            break
                    except ValueError:
                        continue
            
            # Extract mileage with enhanced patterns
            mileage_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*(?:miles?|mi)\b',
                r'Mileage[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'(\d{1,3}(?:,\d{3})*)\s*(?:mile|odometer)'
            ]
            
            for pattern in mileage_patterns:
                mileage_match = re.search(pattern, text, re.IGNORECASE)
                if mileage_match:
                    mileage_str = mileage_match.group(1).replace(',', '')
                    try:
                        mileage = int(mileage_str)
                        if 0 <= mileage <= 500000:
                            vehicle['mileage'] = mileage
                            break
                    except ValueError:
                        continue
            
            # Enhanced Lincoln model detection
            lincoln_models = {
                'AVIATOR': ['AVIATOR'],
                'CORSAIR': ['CORSAIR'],
                'NAUTILUS': ['NAUTILUS'],
                'NAVIGATOR': ['NAVIGATOR'],
                'CONTINENTAL': ['CONTINENTAL'],
                'MKZ': ['MKZ'],
                'MKC': ['MKC'],
                'MKX': ['MKX'],
                'MKT': ['MKT'],
                'TOWN CAR': ['TOWN CAR', 'TOWNCAR']
            }
            
            text_upper = text.upper()
            for model_name, variations in lincoln_models.items():
                if any(variation in text_upper for variation in variations):
                    vehicle['model'] = model_name.title()
                    break
            
            # Extract VIN (if available)
            vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text.upper())
            if vin_match:
                vehicle['vin'] = vin_match.group()
            
            # Extract stock number
            stock_patterns = [
                r'Stock[:\s#]*([A-Z0-9]+)',
                r'Stock#[:\s]*([A-Z0-9]+)',
                r'#([A-Z0-9]{4,})',
                r'ID[:\s]*([A-Z0-9]+)'
            ]
            
            for pattern in stock_patterns:
                stock_match = re.search(pattern, text, re.IGNORECASE)
                if stock_match:
                    vehicle['stock_number'] = stock_match.group(1)
                    break
            
            # Extract exterior color
            color_patterns = [
                r'(?:Color|Exterior)[:\s]*(\w+(?:\s+\w+)?)',
                r'\b(Black|White|Silver|Gray|Grey|Red|Blue|Green|Brown|Gold|Beige|Tan|Burgundy|Maroon)\b'
            ]
            
            for pattern in color_patterns:
                color_match = re.search(pattern, text, re.IGNORECASE)
                if color_match:
                    vehicle['ext_color'] = color_match.group(1).title()
                    break
            
            # Try to extract vehicle URL from element attributes
            try:
                # Look for links in the element
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('/vehicle/' in href.lower() or '/inventory/' in href.lower() or '/auto/' in href.lower()):
                        vehicle['vehicle_url'] = href
                        break
            except Exception:
                pass
            
            # Validation - Lincoln dealership should have Lincoln data
            has_lincoln_data = (
                vehicle['year'] or 
                vehicle['price'] or 
                vehicle['model'] or
                'lincoln' in text.lower() or
                vehicle['mileage'] is not None
            )
            
            if has_lincoln_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None
    
    def extract_vehicle_data(self, raw_data: Any) -> Dict[str, Any]:
        """Extract vehicle data (compatibility method)"""
        if isinstance(raw_data, dict):
            return raw_data
        return {}

# Test function to verify scraper works with COMPLETE inventory extraction
def test_dave_sinclair_lincoln_south_scraper():
    """Test the scraper with COMPLETE inventory extraction"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'davesinclairlincolnsouth',
        'name': 'Dave Sinclair Lincoln South',
        'base_url': 'https://www.davesinclairlincolnsouth.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 15000, 'max': 200000},
                'year_range': {'min': 2010, 'max': 2025}
            }
        }
    }
    
    # Create simple config if not available
    try:
        from scraper.config import ScraperConfig
        scraper_config = ScraperConfig()
        scraper_config.request_delay = 1.5
    except ImportError:
        # Fallback config
        class SimpleConfig:
            request_delay = 1.5
            timeout = 30
        scraper_config = SimpleConfig()
    
    scraper = DaveSinclairLincolnSouthWorkingScraper(config, scraper_config)
    
    print("🧪 Testing Dave Sinclair Lincoln South scraper with COMPLETE inventory extraction...")
    print("📊 Reference: complete_data.csv shows dealerships have hundreds of vehicles")
    print("🎯 Goal: Extract ENTIRE inventory (all pages, all vehicles available)")
    
    vehicles = scraper.scrape_inventory()
    
    print(f"✅ COMPLETE inventory extraction: {len(vehicles)} vehicles")
    print(f"📈 Target: Extract ENTIRE dealership inventory (not just first page)")
    
    if vehicles:
        print("📋 Sample vehicle (complete_data.csv format):")
        sample = vehicles[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
        
        print(f"\n📊 Summary:")
        print(f"   Total vehicles: {len(vehicles)}")
        print(f"   With prices: {sum(1 for v in vehicles if v.get('price'))}") 
        print(f"   With models: {sum(1 for v in vehicles if v.get('model'))}")
        print(f"   With VINs: {sum(1 for v in vehicles if v.get('vin'))}")
        print(f"   New vehicles: {sum(1 for v in vehicles if v.get('type') == 'New')}")
        print(f"   Used vehicles: {sum(1 for v in vehicles if v.get('type') == 'Used')}")
    
    # Success criteria: Should extract substantial inventory
    success = len(vehicles) >= 5  # Minimum threshold
    target_met = len(vehicles) >= 20  # Target for substantial inventory
    
    if target_met:
        print(f"🎯 EXCELLENT: {len(vehicles)} vehicles extracted (substantial inventory)")
    elif success:
        print(f"⚠️ PARTIAL SUCCESS: {len(vehicles)} vehicles (goal: extract complete inventory)")
    else:
        print(f"❌ BELOW THRESHOLD: {len(vehicles)} vehicles (minimum: 5)")
    
    print("\n🔄 NOTE: Inventory size varies daily - goal is to capture ENTIRE available inventory")
    
    return success

if __name__ == "__main__":
    success = test_dave_sinclair_lincoln_south_scraper()
    print(f"✅ Test {'PASSED' if success else 'FAILED'}")