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
utils_dir = os.path.join(parent_dir, 'utils')
base_dir = os.path.join(parent_dir, 'base')
sys.path.append(parent_dir)
sys.path.append(utils_dir)
sys.path.append(base_dir)

# Import inventory verification system
try:
    from inventory_verification_mixin import InventoryVerificationMixin
except ImportError:
    from utils.inventory_verification_mixin import InventoryVerificationMixin

# Try to import base classes, create simple fallbacks if not available
try:
    from dealership_base import DealershipScraperBase
    from exceptions import NetworkError, ParsingError
except ImportError:
    try:
        from base.dealership_base import DealershipScraperBase
        from base.exceptions import NetworkError, ParsingError
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

class BMWofWestStLouisWorkingScraper(DealershipScraperBase, InventoryVerificationMixin):
    """
    WORKING scraper for BMW of West St Louis - uses Algolia search API
    Based on original analysis with complete Algolia integration
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # Algolia configuration (from original analysis)
        self.algolia_app_id = 'SEWJN80HTN'
        self.algolia_api_key = '179608f32563367799314290254e3e44'
        self.algolia_base_url = 'https://sewjn80htn-dsn.algolia.net/1/indexes'
        
        # Index names for different vehicle types (from original)
        self.algolia_indexes = {
            'used': 'bmwofweststlouis_production_inventory_sort_image_type_price_lh',
            'certified': 'bmwofweststlouis-sbm0125_production_inventory_sort_image_type_price_lh', 
            'new': 'bmwofweststlouis_production_inventory_sort_image_type_price_lh'
        }
        
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://www.bmwofweststlouis.com',
            'Referer': 'https://www.bmwofweststlouis.com/'
        }
        
        # Session management
        self.session = requests.Session()
        
        # Chrome driver setup for anti-bot bypass
        self.driver = None
        self.wait = None
        self.use_chrome = False  # Try API first, fallback to Chrome
        
        # Location filter from original (encoded)
        self.location_filter = 'BMW%20of%20West%20St.%20Louis%3Cbr%3E%3Ca%20href%3D%5C%22https%3A%2F%2Fmaps.app.goo.gl%2FQyXQWdf6BV6jobY18%5C%22%20target%3D%5C%22_blank%5C%22%3E14417%20Manchester%20Road%3Cbr%3EManchester%2C%20MO%2063011%3C%2Fa%3E%3Cbr%3E%3Ca%20href%3D%5C%22tel%3A888-291-4102%5C%22%3E888-291-4102%3C%2Fa%3E%22'
    
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
            
            # Step 1: Get expected totals for each vehicle type
            self.logger.info("🔍 STEP 1: Detecting expected inventory totals...")
            try:
                inventory_verification['expected_totals'] = self._get_expected_inventory_totals()
            except Exception as e:
                self.logger.warning(f"Could not get expected totals: {str(e)}")
                inventory_verification['expected_totals'] = {}
            
            # Step 2: Scrape all vehicles
            self.logger.info("📥 STEP 2: Scraping complete inventory...")
            
            # Try Algolia API approach first (faster)
            if not self.use_chrome:
                try:
                    self.logger.info(f"Attempting Algolia API scrape for {self.dealership_name}")
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
        """Algolia API-based scraping method with complete pagination"""
        
        all_vehicles = []
        
        # Scrape all vehicle types (from original analysis)
        vehicle_types = ['used', 'certified', 'new']
        
        for vehicle_type in vehicle_types:
            self.logger.info(f"Scraping {vehicle_type} BMW vehicles")
            
            try:
                vehicles = self._scrape_vehicle_type_api(vehicle_type)
                all_vehicles.extend(vehicles)
                
                # Delay between types
                time.sleep(self.config.request_delay)
                
            except Exception as e:
                self.logger.error(f"Error scraping {vehicle_type} vehicles: {str(e)}")
                continue
        
        self.logger.info(f"API scraping complete: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    
    def _scrape_vehicle_type_api(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles for a specific type using Algolia API with pagination"""
        
        vehicles = []
        page_num = 0  # Algolia uses 0-based pagination
        max_pages = 100  # Safety limit
        
        index_name = self.algolia_indexes[vehicle_type]
        
        while page_num < max_pages:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            try:
                # Build Algolia API request (from original patterns)
                api_url = f"{self.algolia_base_url}/*/queries"
                
                # Build query parameters based on original
                query_params = self._build_algolia_query(vehicle_type, page_num, index_name)
                
                self.logger.info(f"Fetching {vehicle_type} BMW vehicles, page: {page_num}")
                
                response = self.session.post(
                    api_url,
                    headers={
                        **self.headers,
                        'x-algolia-agent': 'Algolia for JavaScript (4.9.1); Browser (lite); JS Helper (3.22.4)',
                        'x-algolia-api-key': self.algolia_api_key,
                        'x-algolia-application-id': self.algolia_app_id
                    },
                    json=query_params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                api_data = response.json()
                
                # Extract vehicles from Algolia response structure
                results = api_data.get('results', [])
                if not results:
                    self.logger.info(f"No results for {vehicle_type} vehicles at page {page_num}")
                    break
                
                # Get first result (main query)
                main_result = results[0]
                hits = main_result.get('hits', [])
                total_pages = main_result.get('nbPages', 1)
                
                if not hits:
                    self.logger.info(f"No more {vehicle_type} vehicles at page {page_num}")
                    break
                
                # Process each vehicle
                page_vehicles = []
                for vehicle_data in hits:
                    processed_vehicle = self._process_algolia_vehicle(vehicle_data, vehicle_type)
                    if processed_vehicle:
                        page_vehicles.append(processed_vehicle)
                        vehicles.append(processed_vehicle)
                
                self.logger.info(f"Page {page_num}: Found {len(page_vehicles)} {vehicle_type} BMW vehicles")
                
                # Check if we've reached the end
                if page_num >= total_pages - 1 or len(hits) < 20:
                    self.logger.info(f"Reached end of {vehicle_type} inventory")
                    break
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed for {vehicle_type} page {page_num}: {str(e)}")
                break
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response for {vehicle_type} page {page_num}: {str(e)}")
                break
            
            page_num += 1
            self.rate_limiter.make_request()
            time.sleep(self.config.request_delay)
        
        return vehicles
    
    def _build_algolia_query(self, vehicle_type: str, page_num: int, index_name: str) -> Dict[str, Any]:
        """Build Algolia query based on original patterns"""
        
        # Base facet filters for location (from original)
        location_filter = f"Location%3A{self.location_filter}"
        
        # Vehicle type specific filters (from original analysis)
        if vehicle_type == 'used':
            type_filters = '%5B%22type%3ACertified%20Pre-Owned%22%2C%22type%3APre-Owned%22%5D'
        elif vehicle_type == 'certified':
            type_filters = '%5B%22make%3ABMW%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%5D'
        else:  # new
            type_filters = '%5B%22type%3ANew%22%5D'
        
        # Construct facetFilters parameter
        facet_filters_param = f"facetFilters=%5B%5B%22{location_filter}%22%5D%2C{type_filters}%5D"
        
        # All facets (from original)
        facets = '%5B%22Custom_NewCount%22%2C%22Loaner_Vehicles%22%2C%22Location%22%2C%22algolia_sort_order%22%2C%22api_id%22%2C%22bedtype%22%2C%22body%22%2C%22cap_one%22%2C%22certified%22%2C%22city_mpg%22%2C%22cylinders%22%2C%22date_in_stock%22%2C%22date_modified%22%2C%22days_in_stock%22%2C%22doors%22%2C%22drivetrain%22%2C%22engine_description%22%2C%22ext_color%22%2C%22ext_color_generic%22%2C%22ext_options%22%2C%22features%22%2C%22features%22%2C%22finance_details%22%2C%22ford_SpecialVehicle%22%2C%22fueltype%22%2C%22hash%22%2C%22hw_mpg%22%2C%22image_type%22%2C%22in_transit_filter%22%2C%22int_color%22%2C%22int_options%22%2C%22lease_details%22%2C%22lightning%22%2C%22lightning.class%22%2C%22lightning.finance_monthly_payment%22%2C%22lightning.isPolice%22%2C%22lightning.isSpecial%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.locations%22%2C%22lightning.locations.meta_location%22%2C%22lightning.status%22%2C%22link%22%2C%22loaner_vehicles_test%22%2C%22location%22%2C%22make%22%2C%22metal_flags%22%2C%22miles%22%2C%22model%22%2C%22model_number%22%2C%22msrp%22%2C%22objectID%22%2C%22our_price%22%2C%22our_price_label%22%2C%22special_field_1%22%2C%22stock%22%2C%22thumbnail%22%2C%22title_vrp%22%2C%22transmission_description%22%2C%22trim%22%2C%22type%22%2C%22vin%22%2C%22year%22%5D'
        
        # Build params string
        params = f"{facet_filters_param}&facets={facets}&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
        
        # Build full query structure
        query = {
            'requests': [
                {
                    'indexName': index_name,
                    'params': params
                }
            ]
        }
        
        return query
    
    def _process_algolia_vehicle(self, vehicle_data: Dict[str, Any], vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Process individual vehicle from Algolia response - NORMALIZED DATA FORMAT"""
        
        try:
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': vehicle_data.get('objectID', ''),  # Original uses objectID as VIN
                'stock_number': vehicle_data.get('stock', ''),
                'year': self._safe_int(vehicle_data.get('year')),
                'make': vehicle_data.get('make', 'BMW'),  # Default to BMW for this dealership
                'model': vehicle_data.get('model', ''),
                'trim': vehicle_data.get('trim', ''),
                'price': None,
                'msrp': None,
                'mileage': self._safe_int(vehicle_data.get('miles')),
                'exterior_color': vehicle_data.get('ext_color', ''),
                'interior_color': vehicle_data.get('int_color', ''),
                'body_style': vehicle_data.get('body', ''),
                'fuel_type': vehicle_data.get('fueltype', ''),
                'transmission': vehicle_data.get('transmission_description', ''),
                'engine': vehicle_data.get('engine_description', ''),
                'original_status': 'Available',
                'normalized_status': 'Available',
                'condition': vehicle_data.get('type', vehicle_type.title()),
                'dealer_name': 'BMW of West St Louis',
                'dealer_id': 'bmwofweststlouis',
                'url': vehicle_data.get('link', ''),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Handle pricing (from original field mappings)
            our_price = vehicle_data.get('our_price')
            if our_price:
                vehicle['price'] = self._safe_int(our_price)
            
            msrp = vehicle_data.get('msrp')
            if msrp:
                vehicle['msrp'] = self._safe_int(msrp)
            
            # Enhanced BMW model detection
            make = vehicle_data.get('make', '').upper()
            if make in ['BMW']:
                vehicle['make'] = 'BMW'
            
            # Common BMW models
            model = vehicle_data.get('model', '').upper()
            bmw_models = {
                '3 Series': ['3 SERIES', '320I', '330I', '340I', 'M3'],
                '4 Series': ['4 SERIES', '430I', '440I', 'M4'],
                '5 Series': ['5 SERIES', '530I', '540I', 'M5'],
                '7 Series': ['7 SERIES', '740I', '750I', 'M760I'],
                'X1': ['X1'],
                'X2': ['X2'],
                'X3': ['X3', 'X3M'],
                'X4': ['X4', 'X4M'],
                'X5': ['X5', 'X5M'],
                'X6': ['X6', 'X6M'],
                'X7': ['X7'],
                'Z4': ['Z4'],
                'i3': ['I3'],
                'i4': ['I4'],
                'iX': ['IX'],
                '2 Series': ['2 SERIES', '230I', 'M2']
            }
            
            for model_name, variations in bmw_models.items():
                if any(variation in model for variation in variations):
                    vehicle['model'] = model_name
                    break
            
            # Handle certified pre-owned status
            if 'Certified Pre-Owned' in vehicle_data.get('type', ''):
                vehicle['condition'] = 'Certified Pre-Owned'
            
            # Validation
            if not vehicle['vin'] and not (vehicle['year'] and vehicle['make'] and vehicle['model']):
                self.logger.warning("Skipping vehicle without sufficient data")
                return None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error processing Algolia vehicle data: {str(e)}")
            return None
    
    def extract_vehicle_data(self, raw_data: Any) -> Dict[str, Any]:
        """Extract vehicle data (compatibility method)"""
        if isinstance(raw_data, dict):
            return self._process_algolia_vehicle(raw_data, 'unknown')
        return {}
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas or dollar signs
            if isinstance(value, str):
                value = re.sub(r'[^\\d]', '', value)
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
            
            # Scrape each vehicle type
            for vehicle_type in ['new', 'used', 'certified']:
                self.logger.info(f"Scraping {vehicle_type} BMW vehicles with Chrome")
                
                vehicles = self._scrape_vehicle_type_chrome(vehicle_type)
                all_vehicles.extend(vehicles)
                
                # Delay between types
                time.sleep(2)
            
        finally:
            # Always cleanup Chrome driver
            self._cleanup_chrome_driver()
        
        return all_vehicles
    
    def _setup_chrome_driver(self):
        """Setup ultra-fast Chrome driver for BMW dealership"""
        
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
    
    def _scrape_vehicle_type_chrome(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles using Chrome driver"""
        
        vehicles = []
        
        try:
            # Navigate to inventory page
            base_url = "https://www.bmwofweststlouis.com"
            if vehicle_type == 'new':
                url = f"{base_url}/new-inventory/"
            elif vehicle_type == 'certified':
                url = f"{base_url}/certified-inventory/"
            else:
                url = f"{base_url}/used-inventory/"
            
            self.logger.info(f"Loading {vehicle_type} BMW inventory page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for vehicle listings
            vehicle_elements = self._find_bmw_vehicle_elements()
            
            for element in vehicle_elements:
                vehicle_data = self._extract_bmw_vehicle_from_element(element, vehicle_type)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            self.logger.info(f"Extracted {len(vehicles)} {vehicle_type} BMW vehicles")
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed for {vehicle_type}: {str(e)}")
        
        return vehicles
    
    def _find_bmw_vehicle_elements(self):
        """Find vehicle listing elements on BMW page"""
        
        # Common selectors for BMW/automotive sites
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
        
        # Fallback: look for any elements with BMW or year patterns
        try:
            all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
            vehicle_elements = []
            
            for element in all_elements[:200]:  # Limit search
                text = element.text.strip()
                if text and ('20' in text and any(model in text.upper() for model in ['BMW', '3 SERIES', '5 SERIES', 'X3', 'X5'])):
                    vehicle_elements.append(element)
                    if len(vehicle_elements) >= 20:  # Limit results
                        break
            
            if vehicle_elements:
                self.logger.info(f"Found {len(vehicle_elements)} potential vehicles via text search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []
    
    def _extract_bmw_vehicle_from_element(self, element, vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from a DOM element for BMW of West St Louis"""
        
        try:
            text = element.text.strip()
            
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': '',
                'stock_number': '',
                'year': None,
                'make': 'BMW',
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
                'condition': vehicle_type.title(),
                'dealer_name': 'BMW of West St Louis',
                'dealer_id': 'bmwofweststlouis',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract year (4 digits starting with 19 or 20)
            year_match = re.search(r'\\b(19|20)\\d{2}\\b', text)
            if year_match:
                vehicle['year'] = int(year_match.group())
            
            # Extract price ($XX,XXX pattern)
            price_match = re.search(r'\\$[\\d,]+', text)
            if price_match:
                price_str = price_match.group().replace('$', '').replace(',', '')
                try:
                    vehicle['price'] = int(price_str)
                except ValueError:
                    pass
            
            # Extract mileage
            mileage_match = re.search(r'(\\d{1,3}(?:,\\d{3})*)\\s*(?:miles?|mi)', text, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                try:
                    vehicle['mileage'] = int(mileage_str)
                except ValueError:
                    pass
            
            # Enhanced BMW model detection
            bmw_models = {
                '3 Series': ['3 SERIES', '320I', '330I', '340I', 'M3'],
                '4 Series': ['4 SERIES', '430I', '440I', 'M4'],
                '5 Series': ['5 SERIES', '530I', '540I', 'M5'],
                '7 Series': ['7 SERIES', '740I', '750I'],
                'X1': ['X1'],
                'X2': ['X2'],
                'X3': ['X3'],
                'X4': ['X4'],
                'X5': ['X5'],
                'X6': ['X6'],
                'X7': ['X7'],
                'Z4': ['Z4'],
                'i3': ['I3'],
                'i4': ['I4'],
                'iX': ['IX'],
                '2 Series': ['2 SERIES', '230I', 'M2']
            }
            
            text_upper = text.upper()
            for model_name, variations in bmw_models.items():
                if any(variation in text_upper for variation in variations):
                    vehicle['model'] = model_name
                    break
            
            # Extract VIN (if available)
            vin_match = re.search(r'\\b[A-HJ-NPR-Z0-9]{17}\\b', text.upper())
            if vin_match:
                vehicle['vin'] = vin_match.group()
            
            # Extract stock number
            stock_patterns = [
                r'Stock[:\\s#]*([A-Z0-9]+)',
                r'Stock#[:\\s]*([A-Z0-9]+)',
                r'#([A-Z0-9]{4,})',
                r'ID[:\\s]*([A-Z0-9]+)'
            ]
            
            for pattern in stock_patterns:
                stock_match = re.search(pattern, text, re.IGNORECASE)
                if stock_match:
                    vehicle['stock_number'] = stock_match.group(1)
                    break
            
            # Extract exterior color
            color_patterns = [
                r'(?:Color|Exterior)[:\\s]*(\\w+(?:\\s+\\w+)?)',
                r'\\b(Black|White|Silver|Gray|Grey|Red|Blue|Green|Brown|Gold|Beige|Tan|Burgundy|Maroon)(?:\\s+(?:Pearl|Metallic|Mica))?\\b'
            ]
            
            for pattern in color_patterns:
                color_match = re.search(pattern, text, re.IGNORECASE)
                if color_match:
                    vehicle['exterior_color'] = color_match.group(1).title()
                    break
            
            # Extract transmission
            transmission_patterns = [
                r'\\b(Automatic|Manual|CVT|8-Speed|6-Speed|Steptronic)(?:\\s+(?:Transmission|Trans))?\\b'
            ]
            
            for pattern in transmission_patterns:
                trans_match = re.search(pattern, text, re.IGNORECASE)
                if trans_match:
                    vehicle['transmission'] = trans_match.group(1).title()
                    break
            
            # Extract engine (BMW engines)
            engine_patterns = [
                r'(\\d+\\.\\d+L?)',
                r'(V6|V8|I4|I6|4-Cyl|6-Cyl|8-Cyl|TwinPower)',
                r'(Turbo|Twin Turbo|Electric|Hybrid)'
            ]
            
            for pattern in engine_patterns:
                engine_match = re.search(pattern, text, re.IGNORECASE)
                if engine_match:
                    vehicle['engine'] = engine_match.group(1)
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
            
            # BMW dealership should have BMW data
            has_bmw_data = (
                vehicle['year'] or 
                vehicle['price'] or 
                vehicle['model'] or
                'bmw' in text.lower() or
                vehicle['mileage'] is not None
            )
            
            if has_bmw_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None

# Test function to verify scraper works
def test_bmw_west_st_louis_scraper():
    """Test the scraper with a small sample"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'bmwofweststlouis',
        'name': 'BMW of West St Louis',
        'base_url': 'https://www.bmwofweststlouis.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 20000, 'max': 200000},
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
    
    scraper = BMWofWestStLouisWorkingScraper(config, scraper_config)
    
    print("🧪 Testing BMW of West St Louis scraper with Algolia API...")
    vehicles = scraper.scrape_inventory()
    
    print(f"✅ Scraped {len(vehicles)} vehicles")
    if vehicles:
        print("📋 Sample vehicle:")
        sample = vehicles[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    return len(vehicles) > 0

if __name__ == "__main__":
    success = test_bmw_west_st_louis_scraper()
    print(f"✅ Test {'PASSED' if success else 'FAILED'}")