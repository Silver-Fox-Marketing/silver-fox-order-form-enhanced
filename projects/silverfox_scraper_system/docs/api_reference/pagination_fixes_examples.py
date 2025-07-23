"""
Pagination Fix Examples for Different Dealership Platforms

This file contains working implementations for fixing pagination issues
in various scraper types based on the successful Dave Sinclair Lincoln South pattern.
"""

import requests
import time
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PaginationMixin:
    """Base mixin for pagination functionality"""
    
    def _navigate_to_next_page(self, page_num: int) -> bool:
        """Universal pagination navigation method"""
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
                '.paging a.next',
                'button.next-page',
                'a.next-link'
            ]
            
            # Method 1: URL parameter modification (most reliable)
            current_url = self.driver.current_url
            
            # Check various URL parameter patterns
            patterns = [
                (r'page=\d+', f'page={page_num}'),
                (r'pt=\d+', f'pt={page_num}'),
                (r'pageNumber=\d+', f'pageNumber={page_num}'),
                (r'p=\d+', f'p={page_num}')
            ]
            
            for pattern, replacement in patterns:
                if re.search(pattern, current_url):
                    new_url = re.sub(pattern, replacement, current_url)
                    if new_url != current_url:
                        self.logger.info(f"Navigating to page {page_num} via URL: {new_url}")
                        self.driver.get(new_url)
                        time.sleep(2)
                        return True
            
            # If no page parameter exists, try adding one
            if '?' not in current_url or not any(p[0] for p in patterns if re.search(p[0], current_url)):
                separator = '&' if '?' in current_url else '?'
                new_url = f"{current_url}{separator}page={page_num}"
                self.logger.info(f"Adding page parameter: {new_url}")
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


class DealerOnAPIPagination:
    """Pagination implementation for DealerOn/Cosmos API platforms"""
    
    def scrape_dealeron_inventory(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape inventory using DealerOn API with proper pagination"""
        vehicles = []
        
        try:
            # First, get dealer and page IDs from the main page
            main_url = f"{self.base_url}/searchall.aspx"
            response = self.session.get(main_url)
            
            # Extract dealer configuration
            dealer_id_match = re.search(r'"dealerId"\s*:\s*"([^"]+)"', response.text)
            page_id_match = re.search(r'"pageId"\s*:\s*"([^"]+)"', response.text)
            
            if not dealer_id_match or not page_id_match:
                self.logger.error("Could not extract dealer configuration")
                return vehicles
            
            dealer_id = dealer_id_match.group(1)
            page_id = page_id_match.group(1)
            
            # Pagination loop
            page_num = 1
            max_pages = 50  # Safety limit
            
            while page_num <= max_pages:
                self.logger.info(f"Fetching page {page_num} for {vehicle_type} vehicles")
                
                # Build API URL
                api_url = f"{self.base_url}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{dealer_id}/{page_id}"
                params = {
                    'pt': page_num,
                    'Dealership': self.dealership_name.replace(' ', '%20'),
                    'host': self.base_url.replace('https://', '').replace('http://', '')
                }
                
                # Add vehicle type filter if needed
                if vehicle_type == 'new':
                    params['condition'] = 'new'
                elif vehicle_type == 'used':
                    params['condition'] = 'used'
                
                # Make API request
                response = self.session.get(api_url, params=params, headers={'Accept': 'application/json'})
                
                if response.status_code != 200:
                    self.logger.error(f"API request failed with status {response.status_code}")
                    break
                
                data = response.json()
                
                # Extract vehicles from current page
                page_vehicles = data.get('Vehicles', [])
                if not page_vehicles:
                    self.logger.info(f"No vehicles found on page {page_num}")
                    break
                
                # Process each vehicle
                for vehicle_data in page_vehicles:
                    extracted = self._extract_dealeron_vehicle(vehicle_data)
                    if extracted:
                        vehicles.append(extracted)
                
                self.logger.info(f"Extracted {len(page_vehicles)} vehicles from page {page_num}")
                
                # Check if more pages exist
                paging_data = data.get('Paging', {}).get('PaginationDataModel', {})
                total_pages = paging_data.get('TotalPages', 1)
                total_count = paging_data.get('TotalCount', 0)
                
                self.logger.info(f"Total pages: {total_pages}, Total vehicles: {total_count}")
                
                if page_num >= total_pages:
                    self.logger.info(f"Reached last page ({page_num} of {total_pages})")
                    break
                
                page_num += 1
                time.sleep(self.config.request_delay)
            
            self.logger.info(f"Completed {vehicle_type} inventory scraping: {len(vehicles)} vehicles")
            return vehicles
            
        except Exception as e:
            self.logger.error(f"Error scraping DealerOn inventory: {str(e)}")
            return vehicles
    
    def _extract_dealeron_vehicle(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from DealerOn API response"""
        try:
            vehicle = {
                'vin': data.get('Vin', ''),
                'stock_number': data.get('StockNumber', ''),
                'year': data.get('ModelYear'),
                'make': data.get('Make', ''),
                'model': data.get('Model', ''),
                'trim': data.get('Trim', ''),
                'price': data.get('Price'),
                'msrp': data.get('MSRP'),
                'mileage': data.get('Mileage'),
                'exterior_color': data.get('ExteriorColor', ''),
                'interior_color': data.get('InteriorColor', ''),
                'body_style': data.get('BodyStyle', ''),
                'fuel_type': data.get('FuelType', ''),
                'transmission': data.get('Transmission', ''),
                'engine': data.get('Engine', ''),
                'condition': data.get('Condition', ''),
                'url': data.get('DetailUrl', ''),
                'images': data.get('Images', []),
                'dealer_name': self.dealership_name,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Clean up price fields
            for price_field in ['price', 'msrp']:
                if vehicle[price_field] and isinstance(vehicle[price_field], str):
                    price_str = re.sub(r'[^\d]', '', vehicle[price_field])
                    vehicle[price_field] = int(price_str) if price_str else None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error extracting DealerOn vehicle: {str(e)}")
            return None


class AlgoliaAPIPagination:
    """Pagination implementation for Algolia-based platforms"""
    
    def scrape_algolia_inventory(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape inventory using Algolia search API with proper pagination"""
        vehicles = []
        
        try:
            # Algolia configuration (usually found in page source)
            algolia_app_id = self._get_algolia_config('app_id')
            algolia_api_key = self._get_algolia_config('api_key')
            algolia_index = self._get_algolia_config('index_name', 'inventory-prod')
            
            if not algolia_app_id or not algolia_api_key:
                self.logger.error("Could not find Algolia configuration")
                return vehicles
            
            # Algolia search endpoint
            algolia_url = f"https://{algolia_app_id}-dsn.algolia.net/1/indexes/*/queries"
            
            headers = {
                'x-algolia-api-key': algolia_api_key,
                'x-algolia-application-id': algolia_app_id,
                'Content-Type': 'application/json'
            }
            
            # Pagination loop
            page_num = 0  # Algolia uses 0-based pagination
            hits_per_page = 50  # Get more results per page
            
            while True:
                self.logger.info(f"Fetching Algolia page {page_num + 1} for {vehicle_type} vehicles")
                
                # Build search query
                facet_filters = []
                if self.dealership_name:
                    facet_filters.append(f"Location:{self.dealership_name}")
                
                if vehicle_type == 'new':
                    facet_filters.append("type:New")
                elif vehicle_type == 'used':
                    facet_filters.append(["type:Used", "type:Certified Used"])
                
                # Algolia request payload
                payload = {
                    "requests": [{
                        "indexName": algolia_index,
                        "params": {
                            "page": page_num,
                            "hitsPerPage": hits_per_page,
                            "facetFilters": [facet_filters] if facet_filters else []
                        }
                    }]
                }
                
                # Make API request
                response = self.session.post(algolia_url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    self.logger.error(f"Algolia request failed with status {response.status_code}")
                    break
                
                data = response.json()
                results = data.get('results', [{}])[0]
                
                # Extract vehicles from current page
                hits = results.get('hits', [])
                if not hits:
                    self.logger.info(f"No more vehicles found on page {page_num + 1}")
                    break
                
                # Process each vehicle
                for hit in hits:
                    extracted = self._extract_algolia_vehicle(hit)
                    if extracted:
                        vehicles.append(extracted)
                
                self.logger.info(f"Extracted {len(hits)} vehicles from page {page_num + 1}")
                
                # Check if more pages exist
                nb_pages = results.get('nbPages', 1)
                nb_hits = results.get('nbHits', 0)
                
                self.logger.info(f"Total pages: {nb_pages}, Total vehicles: {nb_hits}")
                
                if page_num >= nb_pages - 1:  # 0-based index
                    self.logger.info(f"Reached last page ({page_num + 1} of {nb_pages})")
                    break
                
                # Safety check to prevent infinite loops
                if page_num > 100:  # Reasonable limit
                    self.logger.warning("Reached pagination safety limit")
                    break
                
                page_num += 1
                time.sleep(self.config.request_delay)
            
            self.logger.info(f"Completed {vehicle_type} Algolia scraping: {len(vehicles)} vehicles")
            return vehicles
            
        except Exception as e:
            self.logger.error(f"Error scraping Algolia inventory: {str(e)}")
            return vehicles
    
    def _get_algolia_config(self, key: str, default: str = '') -> str:
        """Extract Algolia configuration from page source"""
        try:
            response = self.session.get(self.base_url)
            
            patterns = {
                'app_id': r'algolia[_-]?app[_-]?id["\']?\s*[:=]\s*["\']([^"\']+)',
                'api_key': r'algolia[_-]?api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)',
                'index_name': r'algolia[_-]?index[_-]?name["\']?\s*[:=]\s*["\']([^"\']+)'
            }
            
            pattern = patterns.get(key)
            if pattern:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return default
            
        except Exception as e:
            self.logger.error(f"Error getting Algolia config: {str(e)}")
            return default
    
    def _extract_algolia_vehicle(self, hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from Algolia search result"""
        try:
            vehicle = {
                'vin': hit.get('vin', ''),
                'stock_number': hit.get('stock', ''),
                'year': hit.get('year'),
                'make': hit.get('make', ''),
                'model': hit.get('model', ''),
                'trim': hit.get('trim', ''),
                'price': hit.get('our_price') or hit.get('price'),
                'msrp': hit.get('msrp'),
                'mileage': hit.get('miles') or hit.get('mileage'),
                'exterior_color': hit.get('ext_color', ''),
                'interior_color': hit.get('int_color', ''),
                'body_style': hit.get('body', ''),
                'fuel_type': hit.get('fueltype', ''),
                'transmission': hit.get('transmission_description', ''),
                'engine': hit.get('engine_description', ''),
                'condition': hit.get('type', ''),
                'url': hit.get('link', ''),
                'images': [hit.get('thumbnail')] if hit.get('thumbnail') else [],
                'location': hit.get('location', ''),
                'dealer_name': self.dealership_name,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Clean up numeric fields
            for field in ['price', 'msrp', 'mileage', 'year']:
                if vehicle[field] and isinstance(vehicle[field], str):
                    cleaned = re.sub(r'[^\d]', '', vehicle[field])
                    vehicle[field] = int(cleaned) if cleaned else None
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error extracting Algolia vehicle: {str(e)}")
            return None


class ChromeWebDriverPagination(PaginationMixin):
    """Pagination implementation for WebDriver-based scrapers"""
    
    def scrape_with_pagination(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Scrape vehicles with complete pagination using Chrome WebDriver"""
        vehicles = []
        page_num = 1
        max_pages = 50  # Safety limit
        consecutive_empty_pages = 0
        
        try:
            # Navigate to inventory page
            if vehicle_type == 'new':
                url = f"{self.base_url}/new-inventory"
            elif vehicle_type == 'used':
                url = f"{self.base_url}/used-inventory"
            else:
                url = f"{self.base_url}/inventory"
            
            self.logger.info(f"Starting pagination scrape for {vehicle_type} vehicles at {url}")
            
            while page_num <= max_pages:
                self.logger.info(f"Processing page {page_num}")
                
                # Navigate to page
                if page_num == 1:
                    self.driver.get(url)
                    time.sleep(3)  # Initial page load
                else:
                    # Try to navigate to next page
                    if not self._navigate_to_next_page(page_num):
                        self.logger.info(f"Cannot navigate beyond page {page_num - 1}")
                        break
                
                # Wait for page to load
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(2)  # Additional wait for dynamic content
                except Exception:
                    self.logger.warning(f"Page {page_num} load timeout")
                
                # Find vehicle elements
                vehicle_elements = self._find_vehicle_elements()
                
                if not vehicle_elements:
                    consecutive_empty_pages += 1
                    self.logger.warning(f"No vehicles found on page {page_num}")
                    
                    if consecutive_empty_pages >= 2:
                        self.logger.info("Multiple empty pages encountered, ending pagination")
                        break
                else:
                    consecutive_empty_pages = 0
                
                # Extract vehicles from current page
                page_vehicles = []
                for idx, element in enumerate(vehicle_elements):
                    try:
                        vehicle_data = self._extract_vehicle_from_element(element, vehicle_type)
                        if vehicle_data:
                            page_vehicles.append(vehicle_data)
                            vehicles.append(vehicle_data)
                    except Exception as e:
                        self.logger.error(f"Error extracting vehicle {idx} on page {page_num}: {str(e)}")
                
                self.logger.info(f"Page {page_num}: Extracted {len(page_vehicles)} vehicles (Total: {len(vehicles)})")
                
                # Check if we should continue
                if len(page_vehicles) < 5:  # Likely near end of inventory
                    self.logger.info(f"Page {page_num} has only {len(page_vehicles)} vehicles, may be near end")
                    
                    # Try one more page to be sure
                    if len(page_vehicles) == 0:
                        break
                
                page_num += 1
                time.sleep(self.config.request_delay)
            
            self.logger.info(f"Completed {vehicle_type} pagination: {len(vehicles)} total vehicles from {page_num - 1} pages")
            return vehicles
            
        except Exception as e:
            self.logger.error(f"Error during pagination scrape: {str(e)}")
            return vehicles
    
    def _find_vehicle_elements(self) -> List[Any]:
        """Find all vehicle elements on the current page"""
        # Common selectors for vehicle listings
        selectors = [
            '.vehicle-card',
            '.inventory-item',
            '.vehicle-listing',
            '[data-vehicle]',
            '[data-vehicle-id]',
            '.vehicle-tile',
            '.vehicle-result',
            '.inv-type-used',
            '.inv-type-new',
            '.car-item',
            'article.vehicle',
            '.vdp-tile',
            '.search-result-item',
            '.vehicle-summary',
            '.inventory-vehicle'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.debug(f"Found {len(elements)} vehicles using selector: {selector}")
                    return elements
            except Exception:
                continue
        
        # Fallback: more generic search
        try:
            # Look for elements containing price and year patterns
            all_elements = self.driver.find_elements(By.XPATH, 
                "//div[contains(@class, 'vehicle') or contains(@class, 'inventory') or contains(@class, 'car')]")
            
            vehicle_elements = []
            for element in all_elements[:200]:  # Limit search
                try:
                    text = element.text.strip()
                    # Basic vehicle detection: has year and price
                    if text and re.search(r'\b(19|20)\d{2}\b', text) and re.search(r'\$[\d,]+', text):
                        vehicle_elements.append(element)
                except Exception:
                    continue
            
            if vehicle_elements:
                self.logger.debug(f"Found {len(vehicle_elements)} potential vehicles via fallback search")
                return vehicle_elements
                
        except Exception as e:
            self.logger.warning(f"Fallback element search failed: {str(e)}")
        
        return []


# Example of how to integrate these fixes into existing scrapers:

class FixedColumbiahondaScraper(DealerOnAPIPagination):
    """Fixed Columbia Honda scraper with proper pagination"""
    
    def __init__(self, dealership_config, scraper_config=None):
        # Initialize parent class
        super().__init__()
        self.dealership_name = "Columbia Honda"
        self.base_url = "https://www.columbiahonda.com"
        self.session = requests.Session()
        self.config = scraper_config or type('Config', (), {'request_delay': 2.0})()
        self.logger = type('Logger', (), {
            'info': lambda x: print(f"INFO: {x}"),
            'error': lambda x: print(f"ERROR: {x}"),
            'warning': lambda x: print(f"WARNING: {x}")
        })()
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape complete inventory with fixed pagination"""
        all_vehicles = []
        
        for vehicle_type in ['new', 'used']:
            vehicles = self.scrape_dealeron_inventory(vehicle_type)
            all_vehicles.extend(vehicles)
        
        return all_vehicles


class FixedJoeMachensHyundaiScraper(AlgoliaAPIPagination):
    """Fixed Joe Machens Hyundai scraper with Algolia pagination"""
    
    def __init__(self, dealership_config, scraper_config=None):
        super().__init__()
        self.dealership_name = "Joe Machens Hyundai"
        self.base_url = "https://www.joemachenshyundai.com"
        self.session = requests.Session()
        self.config = scraper_config or type('Config', (), {'request_delay': 1.5})()
        self.logger = type('Logger', (), {
            'info': lambda x: print(f"INFO: {x}"),
            'error': lambda x: print(f"ERROR: {x}"),
            'warning': lambda x: print(f"WARNING: {x}")
        })()
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape complete inventory with fixed Algolia pagination"""
        all_vehicles = []
        
        for vehicle_type in ['new', 'used']:
            vehicles = self.scrape_algolia_inventory(vehicle_type)
            all_vehicles.extend(vehicles)
        
        return all_vehicles


# Test functions
if __name__ == "__main__":
    print("Pagination Fix Examples")
    print("======================")
    print("This file contains implementations for fixing pagination issues in:")
    print("1. DealerOn/Cosmos API platforms")
    print("2. Algolia search platforms")
    print("3. WebDriver-based scrapers")
    print("\nSee the classes above for implementation details.")