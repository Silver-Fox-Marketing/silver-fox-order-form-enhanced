import requests
import time
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os
from bs4 import BeautifulSoup

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

# Import inventory verification system
from inventory_verification_mixin import InventoryVerificationMixin

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

class SuntrupfordkirkwoodWorkingScraper(DealershipScraperBase, InventoryVerificationMixin):
    """
    WORKING scraper for Suntrup Ford Kirkwood - uses DealerOn Cosmos API
    Based on original template with complete DealerOn Cosmos integration and inventory verification
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # DealerOn Cosmos configuration (from original template)
        self.base_url = 'https://www.suntrupfordkirkwood.com'
        self.initial_url = 'https://www.suntrupfordkirkwood.com/searchall.aspx?Dealership=Suntrup%20Ford%20Kirkwood'
        
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Referer': 'https://www.suntrupfordkirkwood.com/'
        }
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # DealerOn Cosmos API variables
        self.dealer_id = None
        self.page_id = None
        
        # Chrome driver setup for anti-bot bypass
        self.driver = None
        self.wait = None
        self.use_chrome = False  # Try API first, fallback to Chrome
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape inventory with COMPLETE inventory verification"""
        
        all_vehicles = []
        inventory_verification = {
            'expected_totals': {},
            'scraped_totals': {},
            'verification_status': {},
            'completeness_percentage': 0.0
        }
        
        try:
            self.logger.info(f"Starting COMPLETE inventory scrape for {self.dealership_name}")
            
            # Step 1: Get expected totals
            self.logger.info("🔍 STEP 1: Detecting expected inventory totals...")
            inventory_verification['expected_totals'] = self._get_expected_inventory_totals()
            
            # Step 2: Scrape all vehicles
            self.logger.info("📥 STEP 2: Scraping complete inventory...")
            
            # Try DealerOn Cosmos API approach first (faster)
            if not self.use_chrome:
                try:
                    self.logger.info(f"Attempting DealerOn Cosmos API scrape for {self.dealership_name}")
                    all_vehicles = self._scrape_with_api()
                    
                    if all_vehicles:
                        self.logger.info(f"API scraping successful: {len(all_vehicles)} vehicles")
                    else:
                        self.logger.warning("API scraping returned no vehicles, switching to Chrome")
                        self.use_chrome = True
                        
                except Exception as e:
                    self.logger.error(f"API scraping failed: {str(e)}")
                    self.logger.info("Falling back to Chrome driver")
                    self.use_chrome = True
            
            # Use Chrome driver approach if needed
            if self.use_chrome:
                try:
                    self.logger.info(f"Starting Chrome-based scrape for {self.dealership_name}")
                    all_vehicles = self._scrape_with_chrome()
                    
                except Exception as e:
                    self.logger.error(f"Chrome scraping failed: {str(e)}")
                    raise
            
            # Step 3: Verify completeness
            self.logger.info("✅ STEP 3: Verifying inventory completeness...")
            inventory_verification = self._verify_inventory_completeness(all_vehicles, inventory_verification)
            
            # Step 4: Cross-verify with dealer website
            self.logger.info("🌐 STEP 4: Cross-verifying with dealer website...")
            website_verification = self.verify_against_dealer_website(len(all_vehicles))
            inventory_verification['website_verification'] = website_verification
            
            # Step 5: Report results
            self._report_inventory_verification(inventory_verification)
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
        
        self.logger.info(f"Scraping complete: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    def _scrape_with_api(self) -> List[Dict[str, Any]]:
        """DealerOn Cosmos API-based scraping method with complete pagination"""
        
        all_vehicles = []
        
        try:
            # Step 1: Initialize DealerOn Cosmos API parameters
            self.logger.info("Initializing DealerOn Cosmos API parameters...")
            if not self._initialize_cosmos_api():
                raise Exception("Failed to initialize DealerOn Cosmos API parameters")
            
            # Step 2: Scrape all pages
            page_num = 1
            max_pages = 100  # Safety limit
            
            while page_num <= max_pages:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()
                
                try:
                    self.logger.info(f"Scraping Ford vehicles page: {page_num}")
                    
                    # Build API URL (from original template pattern)
                    api_url = f"https://www.suntrupfordkirkwood.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{self.dealer_id}/{self.page_id}"
                    
                    # Parameters (from original template)
                    params = {
                        'pt': page_num,
                        'Dealership': 'Suntrup Ford Kirkwood',
                        'host': 'www.suntrupfordkirkwood.com',
                        'pn': '12',
                        'displayCardsShown': '12'
                    }
                    
                    response = self.session.get(
                        api_url,
                        params=params,
                        timeout=self.config.timeout
                    )
                    response.raise_for_status()
                    
                    api_data = response.json()
                    
                    # Extract pagination info
                    paging = api_data.get('Paging', {}).get('PaginationDataModel', {})
                    total_vehicles = paging.get('TotalCount', 0)
                    total_pages = paging.get('TotalPages', 1)
                    page_end = paging.get('PageEnd', 12)
                    
                    # Extract vehicles from this page
                    vehicles = api_data.get('Vehicles', [])
                    if not vehicles:
                        self.logger.info(f"No more vehicles at page {page_num}")
                        break
                    
                    # Process each vehicle
                    page_vehicles = []
                    for vehicle_data in vehicles:
                        processed_vehicle = self._process_cosmos_vehicle(vehicle_data)
                        if processed_vehicle:
                            page_vehicles.append(processed_vehicle)
                            all_vehicles.append(processed_vehicle)
                    
                    self.logger.info(f"Page {page_num}: Found {len(page_vehicles)} Ford vehicles (Total so far: {len(all_vehicles)}, Expected: {total_vehicles}, Total Pages: {total_pages})")
                    
                    # Check if we've reached the end
                    if page_num >= total_pages or len(vehicles) < 12:
                        self.logger.info(f"Reached end of Ford inventory")
                        break
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"API request failed for page {page_num}: {str(e)}")
                    break
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response for page {page_num}: {str(e)}")
                    break
                
                page_num += 1
                self.rate_limiter.make_request()
                time.sleep(self.config.request_delay)
            
        except Exception as e:
            self.logger.error(f"DealerOn Cosmos API scraping failed: {str(e)}")
            raise
        
        self.logger.info(f"API scraping complete: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    def _initialize_cosmos_api(self) -> bool:
        """Initialize DealerOn Cosmos API parameters by parsing initial page"""
        
        try:
            self.logger.info(f"Fetching initial page: {self.initial_url}")
            response = self.session.get(self.initial_url, timeout=self.config.timeout)
            response.raise_for_status()
            
            # Parse HTML to find dealeron_tagging_data script
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the script tag with id 'dealeron_tagging_data'
            script_tag = soup.find('script', id='dealeron_tagging_data')
            if not script_tag or not script_tag.string:
                self.logger.error("Could not find dealeron_tagging_data script tag")
                return False
            
            # Parse JSON data from script
            json_data = json.loads(script_tag.string.strip())
            
            # Extract required parameters
            self.dealer_id = json_data.get('dealerId')
            self.page_id = json_data.get('pageId')
            
            if not self.dealer_id or not self.page_id:
                self.logger.error(f"Missing required parameters: dealer_id={self.dealer_id}, page_id={self.page_id}")
                return False
            
            self.logger.info(f"DealerOn Cosmos API initialized: dealer_id={self.dealer_id}, page_id={self.page_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DealerOn Cosmos API: {str(e)}")
            return False
    
    def _process_cosmos_vehicle(self, vehicle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual vehicle from DealerOn Cosmos API - NORMALIZED DATA FORMAT"""
        
        try:
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': vehicle_data.get('VehicleVin', ''),
                'stock_number': vehicle_data.get('StockNumber', ''),
                'year': self._safe_int(vehicle_data.get('VehicleYear')),
                'make': vehicle_data.get('VehicleMake', ''),
                'model': vehicle_data.get('VehicleModel', ''),
                'trim': vehicle_data.get('Trim', ''),
                'price': None,
                'msrp': None,
                'mileage': self._safe_int(vehicle_data.get('Mileage')),
                'exterior_color': vehicle_data.get('ExteriorColor', ''),
                'interior_color': vehicle_data.get('InteriorColor', ''),
                'body_style': vehicle_data.get('BodyStyle', ''),
                'fuel_type': vehicle_data.get('FuelType', ''),
                'transmission': vehicle_data.get('Transmission', ''),
                'engine': vehicle_data.get('Engine', ''),
                'original_status': 'Available',
                'normalized_status': 'Available',
                'condition': 'Unknown',
                'dealer_name': 'Suntrup Ford Kirkwood',
                'dealer_id': 'suntrupfordkirkwood',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Handle pricing
            msrp = vehicle_data.get('VehicleMsrp')
            if msrp:
                vehicle['msrp'] = self._safe_int(msrp)
            
            # Try various price fields
            for price_field in ['InternetPrice', 'Price', 'SellingPrice', 'VehicleMsrp']:
                if price_field in vehicle_data and vehicle_data[price_field]:
                    vehicle['price'] = self._safe_int(vehicle_data[price_field])
                    break
            
            # Handle status
            status_model = vehicle_data.get('VehicleStatusModel', {})
            if status_model and 'StatusText' in status_model:
                vehicle['original_status'] = status_model['StatusText']
                vehicle['normalized_status'] = status_model['StatusText']
            
            # Determine condition
            condition_text = vehicle_data.get('ConditionText', '').lower()
            if 'new' in condition_text:
                vehicle['condition'] = 'New'
            elif 'certified' in condition_text or 'cpo' in condition_text:
                vehicle['condition'] = 'Certified Pre-Owned'
            elif 'used' in condition_text or 'pre-owned' in condition_text:
                vehicle['condition'] = 'Used'
            
            # Enhanced make normalization for Ford
            make = vehicle_data.get('VehicleMake', '').upper()
            if make in ['FORD']:
                vehicle['make'] = 'Ford'
            elif make in ['LINCOLN']:
                vehicle['make'] = 'Lincoln'
            
            # Enhanced model detection for Ford vehicles
            model = vehicle_data.get('VehicleModel', '').upper()
            
            # Ford models
            ford_models = {
                'F-150': ['F-150', 'F150'],
                'F-250': ['F-250', 'F250'],
                'F-350': ['F-350', 'F350'],
                'F-450': ['F-450', 'F450'],
                'Ranger': ['RANGER'],
                'Maverick': ['MAVERICK'],
                'Mustang': ['MUSTANG'],
                'Escape': ['ESCAPE'],
                'Explorer': ['EXPLORER'],
                'Expedition': ['EXPEDITION'],
                'Edge': ['EDGE'],
                'Bronco': ['BRONCO'],
                'Bronco Sport': ['BRONCO SPORT'],
                'EcoSport': ['ECOSPORT'],
                'Fiesta': ['FIESTA'],
                'Focus': ['FOCUS'],
                'Fusion': ['FUSION'],
                'Taurus': ['TAURUS'],
                'Transit': ['TRANSIT'],
                'E-Series': ['E-SERIES', 'E150', 'E250', 'E350'],
                'Mustang Mach-E': ['MACH-E', 'MUSTANG MACH-E'],
                'F-150 Lightning': ['F-150 LIGHTNING', 'LIGHTNING']
            }
            
            # Lincoln models
            lincoln_models = {
                'Navigator': ['NAVIGATOR'],
                'Aviator': ['AVIATOR'],
                'Corsair': ['CORSAIR'],
                'Nautilus': ['NAUTILUS'],
                'Continental': ['CONTINENTAL'],
                'MKZ': ['MKZ'],
                'MKX': ['MKX'],
                'MKC': ['MKC'],
                'Town Car': ['TOWN CAR']
            }
            
            # Apply model detection based on make
            all_models = {**ford_models, **lincoln_models}
            for model_name, variations in all_models.items():
                if any(variation in model for variation in variations):
                    vehicle['model'] = model_name
                    break
            
            # Build vehicle URL
            if vehicle['vin']:
                vehicle['url'] = f"https://www.suntrupfordkirkwood.com/vehicle/{vehicle['vin']}/"
            
            # Validation
            if not vehicle['vin'] and not (vehicle['year'] and vehicle['make'] and vehicle['model']):
                self.logger.warning("Skipping vehicle without sufficient data")
                return None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error processing DealerOn Cosmos vehicle data: {str(e)}")
            return None
    
    def extract_vehicle_data(self, raw_data: Any) -> Dict[str, Any]:
        """Extract vehicle data (compatibility method)"""
        if isinstance(raw_data, dict):
            return self._process_cosmos_vehicle(raw_data)
        return {}
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas or dollar signs
            if isinstance(value, str):
                value = re.sub(r'[^\d]', '', value)
            return int(float(str(value))) if value else None
        except (ValueError, TypeError):
            return None
    
    # Chrome Driver Methods for Anti-Bot Bypass
    
    def _scrape_with_chrome(self) -> List[Dict[str, Any]]:
        """Chrome-based scraping for anti-bot protected sites"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available - install with: pip install selenium")
        
        all_vehicles = []
        
        try:
            # Setup Chrome driver
            self._setup_chrome_driver()
            
            # Scrape inventory pages
            inventory_pages = [
                f"{self.base_url}/new-inventory/",
                f"{self.base_url}/used-inventory/"
            ]
            
            for page_url in inventory_pages:
                self.logger.info(f"Scraping inventory with Chrome: {page_url}")
                
                vehicles = self._scrape_inventory_page_chrome(page_url)
                all_vehicles.extend(vehicles)
                
                # Delay between pages
                time.sleep(2)
            
        finally:
            # Always cleanup Chrome driver
            self._cleanup_chrome_driver()
        
        return all_vehicles
    
    def _setup_chrome_driver(self):
        """Setup ultra-fast Chrome driver for Ford dealership"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
        
        options = Options()
        
        # Performance optimizations
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
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
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
            
            # Timeouts
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
    
    def _scrape_inventory_page_chrome(self, page_url: str) -> List[Dict[str, Any]]:
        """Scrape inventory page using Chrome driver"""
        
        vehicles = []
        
        try:
            self.logger.info(f"Loading inventory page: {page_url}")
            self.driver.get(page_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for vehicle listings
            vehicle_elements = self._find_ford_vehicle_elements()
            
            for element in vehicle_elements:
                vehicle_data = self._extract_ford_vehicle_from_element(element, page_url)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            self.logger.info(f"Extracted {len(vehicles)} vehicles from page")
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed for page {page_url}: {str(e)}")
        
        return vehicles
    
    def _find_ford_vehicle_elements(self):
        """Find vehicle listing elements on Ford dealership page"""
        
        # Common selectors for automotive sites
        selectors = [
            '.vehicle-card',
            '.inventory-item',
            '.vehicle-listing',
            '[data-vehicle-id]',
            '.vehicle-tile',
            '.vehicle-summary'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.info(f"Found {len(elements)} vehicles using selector: {selector}")
                    return elements[:30]  # Limit for efficiency
            except Exception:
                continue
        
        # Fallback: look for any elements with Ford patterns
        try:
            all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
            vehicle_elements = []
            
            for element in all_elements[:200]:  # Limit search
                text = element.text.strip()
                if text and ('20' in text and any(brand in text.upper() for brand in ['FORD', 'LINCOLN', 'F-150', 'MUSTANG', 'ESCAPE'])):
                    vehicle_elements.append(element)
                    if len(vehicle_elements) >= 20:  # Limit results
                        break
            
            if vehicle_elements:
                self.logger.info(f"Found {len(vehicle_elements)} potential vehicles via text search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []
    
    def _extract_ford_vehicle_from_element(self, element, page_url: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from a DOM element for Suntrup Ford Kirkwood"""
        
        try:
            text = element.text.strip()
            
            # Determine condition from URL
            condition = 'Unknown'
            if '/new-inventory/' in page_url:
                condition = 'New'
            elif '/used-inventory/' in page_url:
                condition = 'Used'
            
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': '',
                'stock_number': '',
                'year': None,
                'make': '',
                'model': '',
                'trim': '',
                'price': None,
                'msrp': None,
                'mileage': None,
                'exterior_color': '',
                'interior_color': '',
                'body_style': '',
                'fuel_type': '',
                'transmission': '',
                'engine': '',
                'original_status': 'Available',
                'normalized_status': 'Available',
                'condition': condition,
                'dealer_name': 'Suntrup Ford Kirkwood',
                'dealer_id': 'suntrupfordkirkwood',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract year (4 digits starting with 19 or 20)
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                vehicle['year'] = int(year_match.group())
            
            # Extract price ($XX,XXX pattern)
            price_match = re.search(r'\$[\d,]+', text)
            if price_match:
                price_str = price_match.group().replace('$', '').replace(',', '')
                try:
                    vehicle['price'] = int(price_str)
                except ValueError:
                    pass
            
            # Extract mileage
            mileage_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:miles?|mi)', text, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                try:
                    vehicle['mileage'] = int(mileage_str)
                except ValueError:
                    pass
            
            # Enhanced make detection for Ford brands
            text_upper = text.upper()
            if 'FORD' in text_upper:
                vehicle['make'] = 'Ford'
            elif 'LINCOLN' in text_upper:
                vehicle['make'] = 'Lincoln'
            
            # Enhanced model detection for Ford vehicles
            model_patterns = {
                # Ford
                'F-150': ['F-150', 'F150'],
                'F-250': ['F-250', 'F250'],
                'F-350': ['F-350', 'F350'],
                'Ranger': ['RANGER'],
                'Maverick': ['MAVERICK'],
                'Mustang': ['MUSTANG'],
                'Escape': ['ESCAPE'],
                'Explorer': ['EXPLORER'],
                'Expedition': ['EXPEDITION'],
                'Edge': ['EDGE'],
                'Bronco': ['BRONCO'],
                'Transit': ['TRANSIT'],
                'Fusion': ['FUSION'],
                'Focus': ['FOCUS'],
                # Lincoln
                'Navigator': ['NAVIGATOR'],
                'Aviator': ['AVIATOR'],
                'Corsair': ['CORSAIR'],
                'Nautilus': ['NAUTILUS']
            }
            
            for model_name, variations in model_patterns.items():
                if any(variation in text_upper for variation in variations):
                    vehicle['model'] = model_name
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
            
            # Extract vehicle URL from element attributes
            try:
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('/vehicle/' in href.lower() or '/inventory/' in href.lower() or '/auto/' in href.lower()):
                        vehicle['url'] = href
                        break
            except Exception:
                pass
            
            # Ford dealership should have Ford data
            has_ford_data = (
                vehicle['year'] or 
                vehicle['price'] or 
                vehicle['model'] or
                any(brand in text.lower() for brand in ['ford', 'lincoln', 'f-150', 'mustang', 'escape']) or
                vehicle['mileage'] is not None
            )
            
            if has_ford_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None

# Test function to verify scraper works
def test_suntrup_ford_kirkwood_scraper():
    """Test the scraper with a small sample"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'suntrupfordkirkwood',
        'name': 'Suntrup Ford Kirkwood',
        'base_url': 'https://www.suntrupfordkirkwood.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 15000, 'max': 120000},
                'year_range': {'min': 2015, 'max': 2025}
            }
        }
    }
    
    # Create simple config if not available
    try:
        from scraper.config import ScraperConfig
        scraper_config = ScraperConfig()
        scraper_config.request_delay = 2.0
    except ImportError:
        # Fallback config
        class SimpleConfig:
            request_delay = 2.0
            timeout = 30
        scraper_config = SimpleConfig()
    
    scraper = SuntrupfordkirkwoodWorkingScraper(config, scraper_config)
    
    print("🧪 Testing Suntrup Ford Kirkwood scraper with DealerOn Cosmos API...")
    vehicles = scraper.scrape_inventory()
    
    print(f"✅ Scraped {len(vehicles)} vehicles")
    if vehicles:
        print("📋 Sample vehicle:")
        sample = vehicles[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    return len(vehicles) > 0

if __name__ == "__main__":
    success = test_suntrup_ford_kirkwood_scraper()
    print(f"✅ Test {'PASSED' if success else 'FAILED'}")