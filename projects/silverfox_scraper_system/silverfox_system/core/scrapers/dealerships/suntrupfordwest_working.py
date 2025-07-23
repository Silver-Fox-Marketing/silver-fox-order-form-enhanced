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
    from ..base.dealership_base import DealershipScraperBase
    from ..base.exceptions import NetworkError, ParsingError
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

class SuntrupFordWestWorkingScraper(DealershipScraperBase):
    """
    WORKING scraper for Suntrup Ford West - based on successful Kirkwood pattern
    Uses DealerOn platform with Chrome driver for anti-bot bypass
    """
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config=None):
        super().__init__(dealership_config, scraper_config)
        
        # Suntrup Ford West configuration (DealerOn platform like Kirkwood)
        self.base_url = 'https://www.suntrupfordwest.com'
        self.search_url = f'{self.base_url}/searchall.aspx?Dealership=Suntrup%20Ford%20West'
        
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
        
        # Chrome driver setup for anti-bot bypass
        self.driver = None
        self.wait = None
        self.use_chrome = False  # Try API first, fallback to Chrome
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape inventory - try DealerOn API first, fallback to Chrome if blocked"""
        
        all_vehicles = []
        
        # Try API approach first (faster)
        if not self.use_chrome:
            try:
                self.logger.info(f"Attempting DealerOn API scrape for {self.dealership_name}")
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
        """Original DealerOn API-based scraping method (same as Kirkwood)"""
        
        all_vehicles = []
        
        try:
            # Step 1: Initialize dealer and page IDs
            if not self._initialize_dealer_info():
                self.logger.warning("Could not initialize dealer info - website may be protected")
                return all_vehicles
            
            self.logger.info(f"Initialized - Dealer ID: {self.dealer_id}, Page ID: {self.page_id}")
            
            # Step 2: Scrape vehicles page by page
            page_num = 1
            max_pages = 200  # Safety limit
            total_vehicles = 0
            
            while page_num <= max_pages:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Build API URL
                api_url = self._build_api_url(page_num)
                
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
                    vehicles = api_data.get('VehiclesModel', {}).get('Vehicles', [])
                    
                    if not vehicles:
                        self.logger.info(f"No vehicles found on page {page_num}")
                        break
                    
                    # Process each vehicle
                    page_vehicles = []
                    for vehicle_data in vehicles:
                        processed_vehicle = self._process_dealeron_vehicle(vehicle_data)
                        if processed_vehicle:
                            page_vehicles.append(processed_vehicle)
                            all_vehicles.append(processed_vehicle)
                    
                    self.logger.info(f"Page {page_num}: Found {len(page_vehicles)} vehicles")
                    total_vehicles += len(page_vehicles)
                    
                    # Check pagination
                    pagination = api_data.get('VehiclesModel', {}).get('Paging', {}).get('PaginationDataModel', {})
                    total_pages = pagination.get('TotalPages', 1)
                    page_end = pagination.get('PageEnd', 0)
                    total_count = pagination.get('TotalCount', 0)
                    
                    self.logger.info(f"Pagination: Page {page_num}/{total_pages}, End: {page_end}, Total: {total_count}")
                    
                    # Stop conditions
                    if page_num >= total_pages or len(vehicles) < 12:
                        self.logger.info(f"Reached end - Page {page_num}, Vehicles: {len(vehicles)}")
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
        
        self.logger.info(f"Scraping complete: {len(all_vehicles)} total vehicles")
        return all_vehicles
    
    def _initialize_dealer_info(self) -> bool:
        """Initialize dealer and page IDs by parsing the search page"""
        
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
    
    def _build_api_url(self, page_num: int) -> str:
        """Build the DealerOn Cosmos API URL"""
        
        base_api_url = f"{self.base_url}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{self.dealer_id}/{self.page_id}"
        
        params = {
            'Dealership': 'Suntrup Ford West',
            'host': 'www.suntrupfordwest.com',
            'pt': str(page_num),
            'pn': '12'  # Items per page
        }
        
        # Build query string
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_api_url}?{param_string}"
    
    def _process_dealeron_vehicle(self, vehicle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual vehicle from DealerOn response - COMPLETE DATA FORMAT"""
        
        try:
            # Complete vehicle data matching complete_data.csv format
            vehicle = {
                'vin': vehicle_data.get('VehicleVin', ''),
                'stock_number': vehicle_data.get('VehicleStock', ''),
                'type': 'New' if vehicle_data.get('VehicleIsNew', False) else 'Used',
                'year': self._safe_int(vehicle_data.get('VehicleYear')),
                'make': vehicle_data.get('VehicleMake', ''),
                'model': vehicle_data.get('VehicleModel', ''),
                'trim': vehicle_data.get('VehicleTrim', ''),
                'ext_color': vehicle_data.get('VehicleExteriorColor', ''),
                'status': 'Available',  # Default status
                'body_style': vehicle_data.get('VehicleBodyType', ''),
                'fuel_type': vehicle_data.get('VehicleFuelType', ''),
                'date_in_stock': vehicle_data.get('VehicleDateInStock', ''),
                'street_address': '11955 Olive Blvd',
                'locality': 'Creve Coeur',
                'postal_code': '63141',
                'region': 'MO',
                'country': 'US',
                'location': 'Suntrup Ford West',
                'vehicle_url': vehicle_data.get('VehicleVdpUrl', ''),
                'mileage': self._safe_int(vehicle_data.get('VehicleOdometer')),
                'drivetrain': vehicle_data.get('VehicleDrivetrain', ''),
                'transmission': vehicle_data.get('VehicleTransmission', ''),
                'interior_color': vehicle_data.get('VehicleInteriorColor', ''),
                'engine': vehicle_data.get('VehicleEngine', ''),
                'condition': 'New' if vehicle_data.get('VehicleIsNew', False) else 'Used'
            }
            
            # Handle status
            status_model = vehicle_data.get('VehicleStatusModel', {})
            vehicle['condition'] = status_model.get('StatusText', 'Unknown')
            vehicle['status'] = status_model.get('StatusText', 'Unknown')
            
            # Handle pricing
            pricing = vehicle_data.get('VehiclePricingModel', {})
            
            # MSRP - with validation
            msrp = pricing.get('VehicleMsrp')
            if msrp:
                msrp_value = self._safe_int(msrp)
                # Validate reasonable MSRP range for Ford vehicles
                if msrp_value and 5000 <= msrp_value <= 150000:
                    vehicle['msrp'] = msrp_value
            
            # Current price - with validation
            current_price = pricing.get('VehicleCurrentPrice')
            if current_price:
                price_value = self._safe_int(current_price)
                # Validate reasonable price range for Ford vehicles
                if price_value and 5000 <= price_value <= 150000:
                    vehicle['price'] = price_value
            
            # Additional dealer info
            vehicle.update({
                'dealer_name': 'Suntrup Ford West',
                'dealer_address': '11955 Olive Blvd',
                'dealer_city': 'Creve Coeur',
                'dealer_state': 'MO',
                'dealer_zip': '63141',
                'dealer_phone': '(314) 569-3600',
                'scraped_at': datetime.now().isoformat()
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
            return self._process_dealeron_vehicle(raw_data)
        return {}
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer with proper price handling"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas or dollar signs
            if isinstance(value, str):
                # Remove $ and commas but preserve decimal points for proper parsing
                cleaned = re.sub(r'[$,]', '', value.strip())
                # Handle decimal prices (convert to cents then back to dollars)
                if '.' in cleaned:
                    return int(float(cleaned))
                else:
                    return int(cleaned) if cleaned.isdigit() else None
            return int(float(str(value))) if value else None
        except (ValueError, TypeError):
            return None
    
    # Chrome Driver Methods for Anti-Bot Bypass (same as Kirkwood)
    
    def _scrape_with_chrome(self) -> List[Dict[str, Any]]:
        """Chrome-based scraping for anti-bot protected sites"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available - install with: pip install selenium")
        
        all_vehicles = []
        
        try:
            # Setup Chrome driver
            self._setup_chrome_driver()
            
            # Scrape each vehicle type
            for vehicle_type in ['new', 'used']:
                self.logger.info(f"Scraping {vehicle_type} vehicles with Chrome")
                
                vehicles = self._scrape_vehicle_type_chrome(vehicle_type)
                all_vehicles.extend(vehicles)
                
                # Delay between types
                time.sleep(2)
            
        finally:
            # Always cleanup Chrome driver
            self._cleanup_chrome_driver()
        
        return all_vehicles
    
    def _setup_chrome_driver(self):
        """Setup ultra-fast, stealth Chrome driver for Suntrup Ford West"""
        
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
        
        options = Options()
        
        # Ultra-fast performance optimizations (same as Kirkwood)
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
    
    def _scrape_vehicle_type_chrome(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles using Chrome driver"""
        
        vehicles = []
        
        try:
            # Navigate to inventory page
            if vehicle_type == 'new':
                url = f"{self.base_url}/searchnew.aspx"
            else:
                url = f"{self.base_url}/searchused.aspx"
            
            self.logger.info(f"Loading {vehicle_type} inventory page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for vehicle listings
            vehicle_elements = self._find_ford_vehicle_elements()
            
            for element in vehicle_elements:
                vehicle_data = self._extract_ford_vehicle_from_element(element, vehicle_type)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            self.logger.info(f"Extracted {len(vehicles)} {vehicle_type} vehicles")
            
        except Exception as e:
            self.logger.error(f"Chrome scraping failed for {vehicle_type}: {str(e)}")
        
        return vehicles
    
    def _find_ford_vehicle_elements(self):
        """Find vehicle listing elements on Suntrup Ford West page"""
        
        # Common selectors for DealerOn sites
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
                    return elements[:50]  # Limit for testing
            except Exception:
                continue
        
        # Fallback: look for any elements with Ford or year patterns
        try:
            all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
            vehicle_elements = []
            
            for element in all_elements[:200]:  # Limit search
                text = element.text.strip()
                if text and ('20' in text and any(model in text.upper() for model in ['FORD', 'F-150', 'ESCAPE', 'EXPLORER', 'EDGE', 'BRONCO', 'MUSTANG'])):
                    vehicle_elements.append(element)
                    if len(vehicle_elements) >= 20:  # Limit results
                        break
            
            if vehicle_elements:
                self.logger.info(f"Found {len(vehicle_elements)} potential vehicles via text search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []
    
    def _extract_ford_vehicle_from_element(self, element, vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from a DOM element for Suntrup Ford West"""
        
        try:
            text = element.text.strip()
            
            # Normalized data structure (only columns needed for normalized_data.csv)
            vehicle = {
                'vin': '',
                'stock_number': '',
                'year': None,
                'make': 'Ford',
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
                'condition': vehicle_type.title(),
                'dealer_name': 'Suntrup Ford West',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract year (4 digits starting with 19 or 20)
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                vehicle['year'] = int(year_match.group())
            
            # Extract price ($XX,XXX pattern) - FIXED to handle decimal prices properly
            price_patterns = [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $XX,XXX.XX or $XX,XXX
                r'Price[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Price: $XX,XXX
                r'MSRP[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'   # MSRP: $XX,XXX
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, text, re.IGNORECASE)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    try:
                        # Convert to integer (remove decimals for final price)
                        price_value = int(float(price_str))
                        # Validate reasonable price range for Ford vehicles
                        if 5000 <= price_value <= 150000:  # $5K - $150K reasonable range
                            vehicle['price'] = price_value
                            break
                    except ValueError:
                        continue
            
            # Extract mileage
            mileage_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:miles?|mi)', text, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                try:
                    vehicle['mileage'] = int(mileage_str)
                except ValueError:
                    pass
            
            # Enhanced Ford model detection
            ford_models = {
                'F-150': ['F-150', 'F150', 'F 150'],
                'F-250': ['F-250', 'F250', 'F 250'],
                'F-350': ['F-350', 'F350', 'F 350'],
                'Escape': ['ESCAPE'],
                'Explorer': ['EXPLORER'],
                'Edge': ['EDGE'],
                'Expedition': ['EXPEDITION'],
                'Mustang': ['MUSTANG'],
                'Fusion': ['FUSION'],
                'Focus': ['FOCUS'],
                'Fiesta': ['FIESTA'],
                'Ranger': ['RANGER'],
                'Bronco': ['BRONCO'],
                'Maverick': ['MAVERICK'],
                'Transit': ['TRANSIT'],
                'EcoSport': ['ECOSPORT'],
                'Lightning': ['LIGHTNING'],
                'Mustang Mach-E': ['MACH-E', 'MACH E']
            }
            
            text_upper = text.upper()
            for model_name, variations in ford_models.items():
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
                r'\b(Black|White|Silver|Gray|Grey|Red|Blue|Green|Brown|Gold|Beige|Tan|Burgundy|Maroon)\b'
            ]
            
            for pattern in color_patterns:
                color_match = re.search(pattern, text, re.IGNORECASE)
                if color_match:
                    vehicle['exterior_color'] = color_match.group(1).title()
                    break
            
            # Extract transmission
            transmission_patterns = [
                r'\b(Automatic|Manual|CVT|6-Speed|8-Speed|10-Speed)\b',
                r'\b(Auto|Std)\b'
            ]
            
            for pattern in transmission_patterns:
                trans_match = re.search(pattern, text, re.IGNORECASE)
                if trans_match:
                    trans_text = trans_match.group(1).upper()
                    if trans_text in ['AUTO', 'AUTOMATIC']:
                        vehicle['transmission'] = 'Automatic'
                    elif trans_text in ['STD', 'MANUAL']:
                        vehicle['transmission'] = 'Manual'
                    else:
                        vehicle['transmission'] = trans_match.group(1).title()
                    break
            
            # Extract engine
            engine_patterns = [
                r'(\d+\.\d+L?)',
                r'(V6|V8|I4|4-Cyl|6-Cyl|8-Cyl|EcoBoost)'
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
            
            # Ford dealership should have Ford data
            has_ford_data = (
                vehicle['year'] or 
                vehicle['price'] or 
                vehicle['model'] or
                'ford' in text.lower() or
                vehicle['mileage'] is not None
            )
            
            if has_ford_data:
                return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error extracting vehicle data: {str(e)}")
        
        return None

# Test function to verify scraper works
def test_suntrup_ford_west_scraper():
    """Test the scraper with a small sample"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {
        'id': 'suntrupfordwest',
        'name': 'Suntrup Ford West',
        'base_url': 'https://www.suntrupfordwest.com',
        'filtering_rules': {
            'conditional_filters': {
                'price_range': {'min': 10000, 'max': 120000},
                'year_range': {'min': 2010, 'max': 2024}
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
    
    scraper = SuntrupFordWestWorkingScraper(config, scraper_config)
    scraper.use_chrome = True  # Force Chrome driver for testing
    
    print("🧪 Testing Suntrup Ford West scraper with Chrome driver...")
    vehicles = scraper.scrape_inventory()
    
    print(f"✅ Scraped {len(vehicles)} vehicles")
    if vehicles:
        print("📋 Sample vehicle:")
        sample = vehicles[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    return len(vehicles) > 0

if __name__ == "__main__":
    success = test_suntrup_ford_west_scraper()
    print(f"✅ Test {'PASSED' if success else 'FAILED'}")