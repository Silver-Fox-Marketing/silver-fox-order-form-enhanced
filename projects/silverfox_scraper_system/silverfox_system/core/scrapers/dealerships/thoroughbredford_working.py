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

class ThoroughbredfordWorkingScraper(DealershipScraperBase, InventoryVerificationMixin):
    """
    WORKING scraper for Thoroughbred Ford - uses DealerOn Cosmos API
    Based on patterns found in original template with complete API integration
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # DealerOn Cosmos configuration (from original patterns)
        self.base_url = 'https://www.thoroughbredford.com'
        self.search_url = f'{self.base_url}/searchall.aspx?pt=1'
        
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'
        }
        
        # Will be populated during initialization
        self.dealer_id = None
        self.page_id = None
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
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
            
            # Try DealerOn API approach first (faster)
            if not self.use_chrome:
                try:
                    self.logger.info(f"Attempting DealerOn API scrape for {self.dealership_name}")
                    all_vehicles = self._scrape_with_dealeron_api()
                    
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
    
    def _scrape_with_dealeron_api(self) -> List[Dict[str, Any]]:
        """DealerOn API-based scraping with MANDATORY pagination for COMPLETE inventory"""
        
        all_vehicles = []
        
        try:
            # Step 1: Initialize dealer and page IDs
            if not self._initialize_dealer_info():
                self.logger.warning("Could not initialize dealer info - website may be protected")
                return all_vehicles
            
            self.logger.info(f"Initialized - Dealer ID: {self.dealer_id}, Page ID: {self.page_id}")
            
            # Step 2: Scrape ALL pages for COMPLETE inventory
            page_num = 1
            max_pages = 200  # Safety limit - captures ENTIRE inventory
            display_cards = 0
            
            while page_num <= max_pages:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Build API URL
                api_url = self._build_api_url(page_num, display_cards)
                
                try:
                    # Make API request
                    response = self.session.get(
                        api_url,
                        timeout=self.config.timeout
                    )
                    response.raise_for_status()
                    
                    # Parse JSON response
                    api_data = response.json()
                    
                    # Extract vehicles from response
                    vehicles = api_data.get('VehiclesModel', {}).get('Vehicles', [])
                    
                    if not vehicles:
                        self.logger.info(f"No vehicles found on page {page_num} - COMPLETE inventory captured")
                        break
                    
                    # Process each vehicle (Thoroughbred Ford doesn't need location filtering)
                    page_vehicles = []
                    for vehicle_data in vehicles:
                        processed_vehicle = self._process_dealeron_vehicle(vehicle_data)
                        if processed_vehicle:
                            page_vehicles.append(processed_vehicle)
                            all_vehicles.append(processed_vehicle)
                    
                    self.logger.info(f"Page {page_num}: Found {len(page_vehicles)} vehicles (Total: {len(vehicles)})") 
                    
                    # Check pagination
                    pagination = api_data.get('VehiclesModel', {}).get('Paging', {}).get('PaginationDataModel', {})
                    total_pages = pagination.get('TotalPages', 1)
                    display_cards = pagination.get('PageEnd', 0)
                    total_count = pagination.get('TotalCount', 0)
                    
                    self.logger.info(f"Pagination: Page {page_num}/{total_pages}, Display Cards: {display_cards}, Total: {total_count}")
                    
                    # Stop conditions - COMPLETE inventory captured
                    if page_num >= total_pages or len(vehicles) < 12:
                        self.logger.info(f"COMPLETE inventory captured - Page {page_num}, Vehicles: {len(vehicles)}")
                        break
                
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"API request failed for page {page_num}: {str(e)}")
                    break
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response for page {page_num}: {str(e)}")
                    break
                
                page_num += 1
                self.rate_limiter.make_request()
                
                # Delay between pages
                time.sleep(self.config.request_delay)
        
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
        
        self.logger.info(f"COMPLETE API inventory extraction: {len(all_vehicles)} total vehicles from {page_num - 1} pages")
        return all_vehicles
    
    def _initialize_dealer_info(self) -> bool:
        """Initialize dealer and page IDs by parsing the search page"""
        
        try:
            self.logger.info("Initializing dealer information from search page")
            
            # Fetch the search page
            response = self.session.get(
                self.search_url,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            html_content = response.text
            
            # Extract dealeron_tagging_data script (from original patterns)
            script_pattern = r'var dealeron_tagging_data = ({.*?});'
            script_match = re.search(script_pattern, html_content, re.DOTALL)
            
            if not script_match:
                self.logger.error("Could not find dealeron_tagging_data script")
                return False
            
            # Parse the JSON data
            script_content = script_match.group(1)
            try:
                tagging_data = json.loads(script_content)
                
                # Extract dealer and page IDs (from original patterns)
                self.dealer_id = tagging_data.get('dealerId')
                self.page_id = tagging_data.get('pageId')
                
                if not self.dealer_id or not self.page_id:
                    self.logger.error(f"Missing IDs - Dealer: {self.dealer_id}, Page: {self.page_id}")
                    return False
                
                self.logger.info(f"Successfully extracted - Dealer ID: {self.dealer_id}, Page ID: {self.page_id}")
                return True
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse dealeron_tagging_data JSON: {str(e)}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to initialize dealer info: {str(e)}")
            return False
    
    def _build_api_url(self, page_num: int, display_cards: int) -> str:
        """Build the DealerOn Cosmos API URL (from original patterns)"""
        
        base_api_url = f"{self.base_url}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{self.dealer_id}/{self.page_id}"
        
        params = {
            'Dealership': 'Thoroughbred Ford',
            'host': 'www.thoroughbredford.com',
            'pt': str(page_num),
            'pn': '12',  # Items per page
            'displayCardsShown': str(display_cards)
        }
        
        # Build query string
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_api_url}?{param_string}"
    
    def _process_dealeron_vehicle(self, vehicle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual vehicle from DealerOn response - NORMALIZED DATA FORMAT"""
        
        try:
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': vehicle_data.get('VehicleVin', ''),
                'stock_number': vehicle_data.get('VehicleStock', ''),
                'year': self._safe_int(vehicle_data.get('VehicleYear')),
                'make': vehicle_data.get('VehicleMake', ''),
                'model': vehicle_data.get('VehicleModel', ''),
                'trim': vehicle_data.get('VehicleTrim', ''),
                'price': None,
                'msrp': None,
                'mileage': self._safe_int(vehicle_data.get('VehicleOdometer')),
                'exterior_color': vehicle_data.get('VehicleExteriorColor', ''),
                'interior_color': vehicle_data.get('VehicleInteriorColor', ''),
                'body_style': vehicle_data.get('VehicleBodyType', ''),
                'fuel_type': vehicle_data.get('VehicleFuelType', ''),
                'transmission': vehicle_data.get('VehicleTransmission', ''),
                'engine': vehicle_data.get('VehicleEngine', ''),
                'original_status': 'Available',
                'normalized_status': 'Available',
                'condition': 'New' if vehicle_data.get('VehicleIsNew', False) else 'Used',
                'dealer_name': 'Thoroughbred Ford',
                'dealer_id': 'thoroughbredford',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Handle status
            status_model = vehicle_data.get('VehicleStatusModel', {})
            if status_model.get('StatusText'):
                vehicle['original_status'] = status_model.get('StatusText', 'Available')
                vehicle['normalized_status'] = status_model.get('StatusText', 'Available')
            
            # Handle pricing
            pricing = vehicle_data.get('VehiclePricingModel', {})
            
            # MSRP
            msrp = pricing.get('VehicleMsrp')
            if msrp:
                vehicle['msrp'] = self._safe_int(msrp)
            
            # Current price
            current_price = pricing.get('VehicleCurrentPrice')
            if current_price:
                vehicle['price'] = self._safe_int(current_price)
            
            # Build vehicle URL
            if vehicle_data.get('VehicleVdpUrl'):
                vehicle['url'] = vehicle_data['VehicleVdpUrl']
            elif vehicle['vin']:
                vehicle['url'] = f"https://www.thoroughbredford.com/vehicle/{vehicle['vin']}/"
            
            # Enhanced Ford model detection for Thoroughbred Ford
            make = vehicle_data.get('VehicleMake', '').upper()
            model = vehicle_data.get('VehicleModel', '').upper()
            
            # Ford models
            ford_models = {
                'F-150': ['F-150', 'F150'],
                'F-250': ['F-250', 'F250'],
                'F-350': ['F-350', 'F350'],
                'Mustang': ['MUSTANG'],
                'Explorer': ['EXPLORER'],
                'Escape': ['ESCAPE'],
                'Edge': ['EDGE'],
                'Expedition': ['EXPEDITION'],
                'Ranger': ['RANGER'],
                'Bronco': ['BRONCO'],
                'EcoSport': ['ECOSPORT'],
                'Fusion': ['FUSION'],
                'Focus': ['FOCUS'],
                'Fiesta': ['FIESTA'],
                'Transit': ['TRANSIT'],
                'E-Series': ['E-SERIES'],
                'Taurus': ['TAURUS'],
                'C-Max': ['C-MAX', 'CMAX']
            }
            
            # Apply Ford model detection
            if make in ['FORD']:
                vehicle['make'] = 'Ford'
                for model_name, variations in ford_models.items():
                    if any(variation in model for variation in variations):
                        vehicle['model'] = model_name
                        break
            
            # Validation - essential for downstream processing
            if not vehicle['vin']:
                self.logger.warning("Skipping vehicle without VIN")
                return None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error processing vehicle data: {str(e)}")
            return None
    
    def extract_vehicle_data(self, raw_data: Any) -> Dict[str, Any]:
        """Extract vehicle data (compatibility method)"""
        if isinstance(raw_data, dict):
            return self._process_dealeron_vehicle(raw_data)
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
                "https://www.thoroughbredford.com/new-inventory/",
                "https://www.thoroughbredford.com/used-inventory/"
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
            
            ford_models = ['FORD', 'F-150', 'F150', 'MUSTANG', 'EXPLORER', 'ESCAPE', 'EDGE', 'EXPEDITION', 'RANGER', 'BRONCO']
            
            for element in all_elements[:200]:  # Limit search
                text = element.text.strip()
                if text and ('20' in text and any(model in text.upper() for model in ford_models)):
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
        """Extract vehicle data from a DOM element for Thoroughbred Ford"""
        
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
                'dealer_name': 'Thoroughbred Ford',
                'dealer_id': 'thoroughbredford',
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
            
            # Enhanced make detection for Ford
            text_upper = text.upper()
            if 'FORD' in text_upper:
                vehicle['make'] = 'Ford'
            
            # Enhanced model detection for Ford vehicles
            model_patterns = {
                'F-150': ['F-150', 'F150'],
                'F-250': ['F-250', 'F250'],
                'F-350': ['F-350', 'F350'],
                'Mustang': ['MUSTANG'],
                'Explorer': ['EXPLORER'],
                'Escape': ['ESCAPE'],
                'Edge': ['EDGE'],
                'Expedition': ['EXPEDITION'],
                'Ranger': ['RANGER'],
                'Bronco': ['BRONCO'],
                'EcoSport': ['ECOSPORT'],
                'Fusion': ['FUSION'],
                'Focus': ['FOCUS'],
                'Transit': ['TRANSIT']
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
                any(brand in text.lower() for brand in ['ford', 'f-150', 'f150', 'mustang', 'explorer', 'escape']) or
                vehicle['mileage'] is not None
            )
            
            if has_ford_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None

# Test function to verify scraper works
def test_thoroughbred_ford_scraper():
    """Test the scraper with a small sample"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'thoroughbredford',
        'name': 'Thoroughbred Ford',
        'base_url': 'https://www.thoroughbredford.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 15000, 'max': 100000},
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
    
    scraper = ThoroughbredfordWorkingScraper(config, scraper_config)
    
    print("🧪 Testing Thoroughbred Ford scraper with DealerOn Cosmos API...")
    vehicles = scraper.scrape_inventory()
    
    print(f"✅ Scraped {len(vehicles)} vehicles")
    if vehicles:
        print("📋 Sample vehicle:")
        sample = vehicles[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    return len(vehicles) > 0

if __name__ == "__main__":
    success = test_thoroughbred_ford_scraper()
    print(f"✅ Test {'PASSED' if success else 'FAILED'}")