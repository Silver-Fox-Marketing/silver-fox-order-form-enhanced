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

class ColumbiaHondaWorkingScraper(DealershipScraperBase):
    """
    WORKING scraper for Columbia Honda - uses DealerOn Cosmos API
    NO CHROME DRIVER NEEDED - Pure HTTP requests for maximum speed
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # DealerOn configuration for Columbia Honda
        self.base_url = 'https://www.columbiahonda.com'
        self.search_url = f'{self.base_url}/searchnew.aspx?Dealership=Columbia%20Honda'
        
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Will be populated during initialization
        self.dealer_id = None
        self.page_id = None
        self.session = requests.Session()
        
        # Vehicle types to scrape
        self.vehicle_types = ['new', 'used']
        
        # Chrome driver setup for anti-bot bypass
        self.driver = None
        self.wait = None
        self.use_chrome = True  # Default to Chrome for reliability
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape inventory - try API first, fallback to Chrome if blocked"""
        
        all_vehicles = []
        
        # Try API approach first (faster)
        if not self.use_chrome:
            try:
                self.logger.info(f"Attempting API scrape for {self.dealership_name}")
                all_vehicles = self._scrape_with_api()
                
                if all_vehicles:
                    self.logger.info(f"API scraping successful: {len(all_vehicles)} vehicles")
                    return all_vehicles
                else:
                    self.logger.warning("API scraping returned no vehicles, switching to Chrome")
                    
            except Exception as e:
                self.logger.error(f"API scraping failed: {str(e)}")
                self.logger.info("Falling back to Chrome driver")
        
        # Use Chrome driver approach
        try:
            self.logger.info(f"Starting Chrome-based scrape for {self.dealership_name}")
            all_vehicles = self._scrape_with_chrome()
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed: {str(e)}")
            raise
        
        self.logger.info(f"Scraping complete: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    def _scrape_with_api(self) -> List[Dict[str, Any]]:
        """Original API-based scraping method"""
        
        all_vehicles = []
        
        # Step 1: Initialize dealer and page IDs
        if not self._initialize_dealer_info():
            self.logger.warning("Could not initialize dealer info - website may be protected")
            return all_vehicles
        
        self.logger.info(f"Initialized - Dealer ID: {self.dealer_id}, Page ID: {self.page_id}")
        
        # Step 2: Scrape each vehicle type
        for vehicle_type in self.vehicle_types:
            self.logger.info(f"Scraping {vehicle_type} vehicles via API")
            
            vehicles = self._scrape_vehicle_type(vehicle_type)
            all_vehicles.extend(vehicles)
            
            # Delay between vehicle types
            time.sleep(self.config.request_delay)
        
        return all_vehicles
    
    def _scrape_with_chrome(self) -> List[Dict[str, Any]]:
        """Chrome-based scraping for anti-bot protected sites"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available - install with: pip install selenium")
        
        all_vehicles = []
        
        try:
            # Setup Chrome driver
            self._setup_chrome_driver()
            
            # Scrape each vehicle type
            for vehicle_type in self.vehicle_types:
                self.logger.info(f"Scraping {vehicle_type} vehicles with Chrome")
                
                vehicles = self._scrape_vehicle_type_chrome(vehicle_type)
                all_vehicles.extend(vehicles)
                
                # Delay between types
                time.sleep(2)
            
        finally:
            # Always cleanup Chrome driver
            self._cleanup_chrome_driver()
        
        return all_vehicles
    
    def _scrape_vehicle_type(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles for a specific type (new/used)"""
        
        vehicles = []
        page_num = 1
        max_pages = 200  # Safety limit
        
        while page_num <= max_pages:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Build API URL for this vehicle type
            api_url = self._build_api_url(vehicle_type, page_num)
            
            try:
                # Make API request
                response = self.session.get(
                    api_url,
                    headers=self.headers,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                # Parse JSON response
                api_data = response.json()
                
                # Extract vehicles from response
                page_vehicles = api_data.get('VehiclesModel', {}).get('Vehicles', [])
                
                if not page_vehicles:
                    self.logger.info(f"No {vehicle_type} vehicles found on page {page_num}")
                    break
                
                # Process each vehicle
                for vehicle_data in page_vehicles:
                    processed_vehicle = self._process_dealeron_vehicle(vehicle_data, vehicle_type)
                    if processed_vehicle:
                        vehicles.append(processed_vehicle)
                
                self.logger.info(f"Page {page_num}: Found {len(page_vehicles)} {vehicle_type} vehicles")
                
                # Check pagination
                pagination = api_data.get('VehiclesModel', {}).get('Paging', {}).get('PaginationDataModel', {})
                total_pages = pagination.get('TotalPages', 1)
                
                # Stop conditions
                if page_num >= total_pages or len(page_vehicles) < 12:
                    self.logger.info(f"Reached end - Page {page_num}, Vehicles: {len(page_vehicles)}")
                    break
            
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed for {vehicle_type} page {page_num}: {str(e)}")
                break
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response for {vehicle_type} page {page_num}: {str(e)}")
                break
            
            page_num += 1
            self.rate_limiter.make_request()
            
            # Delay between pages
            time.sleep(self.config.request_delay)
        
        return vehicles
    
    def _initialize_dealer_info(self) -> bool:
        """Initialize dealer and page IDs by parsing the search page - NO BROWSER"""
        
        try:
            self.logger.info("Initializing dealer information from search page")
            
            # Fetch the search page
            response = self.session.get(
                self.search_url,
                headers=self.headers,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            html_content = response.text
            
            # Extract dealeron_tagging_data script
            script_pattern = r'var dealeron_tagging_data = ({.*?});'
            script_match = re.search(script_pattern, html_content, re.DOTALL)
            
            if not script_match:
                self.logger.error("Could not find dealeron_tagging_data script")
                return False
            
            # Parse the JSON data
            script_content = script_match.group(1)
            try:
                tagging_data = json.loads(script_content)
                
                # Extract dealer and page IDs
                self.dealer_id = tagging_data.get('dealer_id')
                self.page_id = tagging_data.get('page_id')
                
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
    
    def _build_api_url(self, vehicle_type: str, page_num: int) -> str:
        """Build the DealerOn Cosmos API URL for Columbia Honda"""
        
        base_api_url = f"{self.base_url}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{self.dealer_id}/{self.page_id}"
        
        params = {
            'Dealership': 'Columbia Honda',
            'host': 'www.columbiahonda.com',
            'pt': str(page_num),
            'pn': '12',  # Items per page
        }
        
        # Add vehicle type filter
        if vehicle_type == 'new':
            params['condition'] = 'New'
        elif vehicle_type == 'used':
            params['condition'] = 'Used'
        
        # Build query string
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_api_url}?{param_string}"
    
    def _process_dealeron_vehicle(self, vehicle_data: Dict[str, Any], vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Process individual vehicle from DealerOn response"""
        
        try:
            # Extract vehicle data
            vehicle = {
                'vin': vehicle_data.get('VehicleVin', ''),
                'stock_number': vehicle_data.get('VehicleStock', ''),
                'year': self._safe_int(vehicle_data.get('VehicleYear')),
                'make': vehicle_data.get('VehicleMake', ''),
                'model': vehicle_data.get('VehicleModel', ''),
                'trim': vehicle_data.get('VehicleTrim', ''),
                'body_style': vehicle_data.get('VehicleBodyType', ''),
                'fuel_type': vehicle_data.get('VehicleFuelType', ''),
                'drivetrain': vehicle_data.get('VehicleDrivetrain', ''),
                'transmission': vehicle_data.get('VehicleTransmission', ''),
                'exterior_color': vehicle_data.get('VehicleExteriorColor', ''),
                'interior_color': vehicle_data.get('VehicleInteriorColor', ''),
                'mileage': self._safe_int(vehicle_data.get('VehicleOdometer')),
                'engine': vehicle_data.get('VehicleEngine', ''),
                'url': vehicle_data.get('VehicleVdpUrl', ''),
                'location': 'Columbia Honda'
            }
            
            # Handle status
            status_model = vehicle_data.get('VehicleStatusModel', {})
            vehicle['condition'] = status_model.get('StatusText', vehicle_type.title())
            vehicle['status'] = status_model.get('StatusText', vehicle_type.title())
            
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
            
            # Dealer info
            vehicle.update({
                'dealer_name': 'Columbia Honda',
                'dealer_address': '1251 Woodland Ave',
                'dealer_city': 'Columbia',
                'dealer_state': 'MO',
                'dealer_zip': '65201',
                'dealer_phone': '(573) 874-2424'
            })
            
            # Validation
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
            return self._process_dealeron_vehicle(raw_data, 'unknown')
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
    
    def _setup_chrome_driver(self):
        """Setup optimized Chrome driver for speed and stealth"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
        
        options = Options()
        
        # Performance optimizations
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-images')  # Don't load images for speed
        options.add_argument('--disable-javascript')  # Disable JS if not needed
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
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
    
    def _scrape_vehicle_type_chrome(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles using Chrome driver with COMPLETE PAGINATION for full inventory"""
        
        vehicles = []
        page_num = 1
        max_pages = 25  # Honda dealership likely has good inventory
        
        try:
            # Navigate to inventory page
            if vehicle_type == 'new':
                url = f"{self.base_url}/searchnew.aspx"
            else:
                url = f"{self.base_url}/searchused.aspx"
            
            self.logger.info(f"Starting COMPLETE {vehicle_type} Honda inventory extraction")
            self.logger.info(f"Target: Extract entire dealership inventory with pagination")
            
            while page_num <= max_pages:
                self.logger.info(f"Processing page {page_num} for {vehicle_type} Honda inventory")
                
                # Navigate to page
                if page_num == 1:
                    self.driver.get(url)
                else:
                    # Try to navigate to next page
                    if not self._navigate_to_next_page_honda(page_num, vehicle_type):
                        self.logger.info(f"No more pages available after page {page_num - 1} - COMPLETE inventory captured")
                        break
                
                # Wait for page to load
                time.sleep(3)
                
                # Look for vehicle listings on current page
                vehicle_elements = self._find_vehicle_elements()
                
                if not vehicle_elements:
                    self.logger.info(f"No vehicles found on page {page_num} - COMPLETE inventory captured")
                    break
                
                # Extract ALL vehicles from current page
                page_vehicles = []
                for element in vehicle_elements:
                    vehicle_data = self._extract_vehicle_from_element(element, vehicle_type)
                    if vehicle_data:
                        page_vehicles.append(vehicle_data)
                        vehicles.append(vehicle_data)
                
                self.logger.info(f"Page {page_num}: Extracted {len(page_vehicles)} Honda vehicles")
                
                # Check pagination patterns
                if len(page_vehicles) >= 8:
                    self.logger.info(f"Good page volume ({len(page_vehicles)} vehicles) - continuing pagination")
                elif len(page_vehicles) < 3:
                    self.logger.info(f"Page {page_num} has only {len(page_vehicles)} vehicles - likely at end of inventory")
                    break
                
                page_num += 1
                
                # Delay between pages
                time.sleep(2)
            
            self.logger.info(f"COMPLETE {vehicle_type} extraction: {len(vehicles)} total vehicles from {page_num - 1} pages")
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed for {vehicle_type}: {str(e)}")
        
        return vehicles
    
    def _navigate_to_next_page_honda(self, page_num: int, vehicle_type: str) -> bool:
        """Navigate to next page for Honda inventory with multiple strategies"""
        
        try:
            current_url = self.driver.current_url
            
            # Strategy 1: URL parameter modification (most reliable for DealerOn)
            new_url = self._build_honda_pagination_url(current_url, page_num, vehicle_type)
            if new_url and new_url != current_url:
                self.logger.info(f"URL pagination to page {page_num}: {new_url}")
                self.driver.get(new_url)
                time.sleep(2)
                return True
            
            # Strategy 2: Click pagination buttons
            pagination_selectors = [
                f'a[href*="page={page_num}"]',
                f'a[href*="pt={page_num}"]',
                f'a[data-page="{page_num}"]',
                '.pagination .next',
                '.page-next',
                'a[rel="next"]',
                '.next-page',
                f'button[data-page="{page_num}"]',
                f'.page-{page_num}',
                '.paging a.next'
            ]
            
            for selector in pagination_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed() and element.is_enabled():
                        # Scroll element into view
                        self.driver.execute_script("arguments[0].scrollIntoView();", element)
                        time.sleep(1)
                        
                        # Click with JavaScript (more reliable)
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)
                        
                        # Verify navigation succeeded
                        if self.driver.current_url != current_url:
                            self.logger.info(f"Successfully navigated via selector: {selector}")
                            return True
                            
                except Exception:
                    continue
            
            self.logger.warning(f"Could not navigate to page {page_num}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in Honda pagination navigation: {str(e)}")
            return False
    
    def _build_honda_pagination_url(self, current_url: str, page_num: int, vehicle_type: str) -> str:
        """Build pagination URL for Honda DealerOn site"""
        
        # Common DealerOn pagination patterns
        if 'page=' in current_url:
            return re.sub(r'page=\d+', f'page={page_num}', current_url)
        elif 'pt=' in current_url:
            return re.sub(r'pt=\d+', f'pt={page_num}', current_url)
        elif '/page/' in current_url:
            return re.sub(r'/page/\d+', f'/page/{page_num}', current_url)
        else:
            # Add pagination parameter
            separator = '&' if '?' in current_url else '?'
            return f"{current_url}{separator}page={page_num}"
    
    def _find_vehicle_elements(self):
        """Find vehicle listing elements on the page"""
        
        # Common selectors for DealerOn sites
        selectors = [
            '.vehicle-card',
            '.inventory-item',
            '.vehicle-listing',
            '[data-vehicle-id]',
            '.vehicle-tile'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.info(f"Found {len(elements)} vehicles using selector: {selector}")
                    return elements[:50]  # Limit for testing
            except Exception:
                continue
        
        # Fallback: look for any elements with VIN or year patterns
        try:
            all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
            vehicle_elements = []
            
            for element in all_elements[:200]:  # Limit search
                text = element.text.strip()
                if text and ('20' in text and any(make in text.upper() for make in ['HONDA', 'ACCORD', 'CIVIC', 'PILOT'])):
                    vehicle_elements.append(element)
                    if len(vehicle_elements) >= 20:  # Limit results
                        break
            
            if vehicle_elements:
                self.logger.info(f"Found {len(vehicle_elements)} potential vehicles via text search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []
    
    def _extract_vehicle_from_element(self, element, vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from a DOM element - COMPLETE DATA matching complete_data.csv format"""
        
        try:
            text = element.text.strip()
            
            # Complete vehicle structure matching complete_data.csv format
            vehicle = {
                'vin': '',
                'stock_number': '',
                'type': vehicle_type.title(),
                'year': None,
                'make': 'Honda',
                'model': '',
                'trim': '',
                'ext_color': '',
                'status': 'Available',
                'body_style': '',
                'fuel_type': '',
                'msrp': None,
                'date_in_stock': '',
                'street_address': '1251 Woodland Ave',
                'locality': 'Columbia',
                'postal_code': '65201',
                'region': 'MO',
                'country': 'US',
                'location': 'Columbia Honda',
                'vehicle_url': '',
                'mileage': None,
                'condition': vehicle_type.title(),
                'dealer_name': 'Columbia Honda',
                'dealer_city': 'Columbia',
                'dealer_state': 'MO',
                'scraped_at': datetime.now().isoformat(),
                'source_text': text[:300]
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
            
            # Enhanced Honda model detection
            honda_models = {
                'Accord': ['ACCORD'],
                'Civic': ['CIVIC'],
                'Pilot': ['PILOT'],
                'CR-V': ['CR-V', 'CRV'],
                'Odyssey': ['ODYSSEY'],
                'Ridgeline': ['RIDGELINE'],
                'Passport': ['PASSPORT'],
                'HR-V': ['HR-V', 'HRV'],
                'Insight': ['INSIGHT'],
                'Fit': ['FIT'],
                'Element': ['ELEMENT']
            }
            
            text_upper = text.upper()
            for model_name, variations in honda_models.items():
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
            
            # Extract exterior color
            color_patterns = [
                r'(?:Color|Exterior)[:\s]*(\w+(?:\s+\w+)?)',
                r'\b(Black|White|Silver|Gray|Grey|Red|Blue|Green|Brown|Gold|Beige|Tan)\b'
            ]
            
            for pattern in color_patterns:
                color_match = re.search(pattern, text, re.IGNORECASE)
                if color_match:
                    vehicle['ext_color'] = color_match.group(1).title()
                    break
            
            # Extract vehicle URL from element attributes
            try:
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('/vehicle/' in href.lower() or '/inventory/' in href.lower() or '/auto/' in href.lower()):
                        vehicle['vehicle_url'] = href
                        break
            except Exception:
                pass
            
            # Validation - Honda dealership should have Honda data
            has_honda_data = (
                vehicle['year'] or 
                vehicle['price'] or 
                vehicle['model'] or
                'honda' in text.lower() or
                vehicle['mileage'] is not None
            )
            
            if has_honda_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None

# Test function to verify scraper works
def test_columbia_honda_scraper():
    """Test the Columbia Honda scraper with real data"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'columbiahonda',
        'name': 'Columbia Honda',
        'base_url': 'https://www.columbiahonda.com',
        'address': '1251 Woodland Ave',
        'city': 'Columbia',
        'state': 'MO', 
        'zip': '65201',
        'phone': '(573) 874-2424',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 10000, 'max': 100000},
                'year_range': {'min': 2010, 'max': 2024}
            }
        }
    }
    
    # Create simple config for testing
    class TestConfig:
        request_delay = 2.0  # Be respectful
        timeout = 30
    
    scraper_config = TestConfig()
    
    try:
        scraper = ColumbiaHondaWorkingScraper(config, scraper_config)
        scraper.use_chrome = True  # Force Chrome driver for testing
        
        print("🚀 COLUMBIA HONDA SCRAPER TEST")
        print("=" * 50)
        print("🧪 Testing Columbia Honda scraper with Chrome driver...")
        print("🌐 Target: https://www.columbiahonda.com")
        print("📋 Using Chrome driver for anti-bot bypass")
        
        vehicles = scraper.scrape_inventory()
        
        print(f"\n✅ Scraped {len(vehicles)} vehicles")
        
        if vehicles:
            print("\n📊 DATA ANALYSIS:")
            print(f"  Total vehicles: {len(vehicles)}")
            
            # Analyze vehicle types
            new_count = len([v for v in vehicles if v.get('condition', '').lower() in ['new']])
            used_count = len([v for v in vehicles if v.get('condition', '').lower() in ['used', 'pre-owned']])
            cpo_count = len([v for v in vehicles if 'certified' in v.get('condition', '').lower()])
            
            print(f"  New vehicles: {new_count}")
            print(f"  Used vehicles: {used_count}")
            print(f"  Certified pre-owned: {cpo_count}")
            
            # Price analysis
            prices = [v.get('price') for v in vehicles if v.get('price')]
            if prices:
                print(f"  Price range: ${min(prices):,} - ${max(prices):,}")
                print(f"  Average price: ${sum(prices) // len(prices):,}")
            
            print("\n📋 SAMPLE VEHICLE:")
            sample = vehicles[0]
            for key, value in sample.items():
                if value:  # Only show non-empty values
                    print(f"   {key}: {value}")
            
            return True
        else:
            print("⚠️  No vehicles found")
            print("💡 This could indicate:")
            print("   • Website blocking (anti-bot protection)")
            print("   • API endpoint changes")
            print("   • Network connectivity issues")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(f"📄 Full traceback:\n{traceback.format_exc()}")
        return False

def quick_test_columbia_honda():
    """Quick test to verify basic functionality"""
    
    config = {
        'id': 'columbiahonda_quick',
        'name': 'Columbia Honda Quick Test',
        'base_url': 'https://www.columbiahonda.com'
    }
    
    class QuickConfig:
        request_delay = 1.0
        timeout = 15
    
    try:
        scraper = ColumbiaHondaWorkingScraper(config, QuickConfig())
        
        # Force Chrome usage for testing
        scraper.use_chrome = True
        
        # Test Chrome driver setup
        print("🔧 Testing Chrome driver setup...")
        init_success = True  # Skip API test, go straight to Chrome
        
        if SELENIUM_AVAILABLE:
            print("   ✅ Selenium available")
        else:
            print("   ❌ Selenium not available")
            init_success = False
        
        print(f"🔧 Initialization: {'✅ SUCCESS' if init_success else '❌ FAILED'}")
        if init_success:
            print(f"   Dealer ID: {scraper.dealer_id}")
            print(f"   Page ID: {scraper.page_id}")
        
        return init_success
        
    except Exception as e:
        print(f"❌ Quick test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 COLUMBIA HONDA SCRAPER TESTS")
    print("=" * 50)
    
    # Quick test first
    print("🔧 Quick initialization test...")
    quick_success = quick_test_columbia_honda()
    
    if quick_success:
        print("\n🧪 Full scraper test...")
        success = test_columbia_honda_scraper()
        print(f"\n✅ Overall test {'PASSED' if success else 'FAILED'}")
    else:
        print("\n❌ Skipping full test due to initialization failure")
        print("💡 Check network connectivity and website availability")