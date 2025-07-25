#!/usr/bin/env python3
"""
Network Utilities for Silver Fox Scraper System
===============================================

Provides robust network handling, retry mechanisms, and fallback strategies
for API calls across all scraper platforms.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import time
import requests
import logging
from typing import Dict, List, Any, Optional, Callable
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class NetworkHandler:
    """Enhanced network handler with retry mechanisms and fallback strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = self._create_robust_session()
    
    def _create_robust_session(self) -> requests.Session:
        """Create a requests session with retry configuration"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        # Mount adapters with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def robust_api_call(self, 
                       url: str, 
                       method: str = "GET",
                       headers: Optional[Dict[str, str]] = None,
                       json_data: Optional[Dict[str, Any]] = None,
                       params: Optional[Dict[str, Any]] = None,
                       timeout: int = 30,
                       max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Make a robust API call with retry logic and error handling
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            headers: Request headers
            json_data: JSON payload for POST requests
            params: URL parameters for GET requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response JSON data or None if all attempts fail
        """
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"📡 API call attempt {attempt + 1}/{max_retries + 1}: {url}")
                
                # Make the request
                if method.upper() == "POST":
                    response = self.session.post(
                        url,
                        headers=headers,
                        json=json_data,
                        params=params,
                        timeout=timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=timeout
                    )
                
                # Check response status
                if response.status_code == 200:
                    self.logger.info(f"✅ API call successful: {response.status_code}")
                    return response.json()
                elif response.status_code in [429, 500, 502, 503, 504]:
                    self.logger.warning(f"⚠️ Retryable error {response.status_code}, attempt {attempt + 1}")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                else:
                    self.logger.error(f"❌ Non-retryable error: {response.status_code}")
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"⚠️ Connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    self.logger.error("❌ All connection attempts failed")
                    return None
                    
            except requests.exceptions.Timeout as e:
                self.logger.error(f"⏰ Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    self.logger.error("❌ All timeout attempts failed")
                    return None
                    
            except Exception as e:
                self.logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return None
        
        return None
    
    def test_connectivity(self, urls: List[str]) -> Dict[str, bool]:
        """Test connectivity to multiple URLs"""
        results = {}
        
        for url in urls:
            try:
                response = self.session.head(url, timeout=10)
                results[url] = response.status_code < 400
                self.logger.info(f"🔗 {url}: {'✅ Reachable' if results[url] else '❌ Unreachable'}")
            except Exception as e:
                results[url] = False
                self.logger.error(f"🔗 {url}: ❌ Error - {e}")
        
        return results


class AlgoliaAPIHandler(NetworkHandler):
    """Specialized handler for Algolia API calls with fallback strategies"""
    
    def __init__(self, app_id: str, api_key: str):
        super().__init__()
        self.app_id = app_id
        self.api_key = api_key
        
        # Multiple endpoint patterns to try
        self.endpoint_patterns = [
            f"https://{app_id}-dsn.algolia.net/1/indexes/{{index_name}}/query",
            f"https://{app_id}.algolia.net/1/indexes/{{index_name}}/query",
            f"https://{app_id}-1.algolianet.com/1/indexes/{{index_name}}/query"
        ]
    
    def search_with_fallback(self, 
                           index_name: str, 
                           query_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform Algolia search with multiple endpoint fallback
        
        Args:
            index_name: Algolia index name
            query_params: Search parameters
            
        Returns:
            Search results or None if all endpoints fail
        """
        headers = {
            'X-Algolia-API-Key': self.api_key,
            'X-Algolia-Application-Id': self.app_id,
            'Content-Type': 'application/json'
        }
        
        for endpoint_pattern in self.endpoint_patterns:
            endpoint = endpoint_pattern.format(index_name=index_name)
            
            self.logger.info(f"🔍 Trying Algolia endpoint: {endpoint}")
            
            result = self.robust_api_call(
                url=endpoint,
                method="POST",
                headers=headers,
                json_data=query_params,
                timeout=30,
                max_retries=2
            )
            
            if result:
                self.logger.info(f"✅ Algolia search successful via: {endpoint}")
                return result
            else:
                self.logger.warning(f"⚠️ Algolia endpoint failed: {endpoint}")
        
        self.logger.error("❌ All Algolia endpoints failed")
        return None


class DealerOnAPIHandler(NetworkHandler):
    """Specialized handler for DealerOn API calls with endpoint discovery"""
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        
        # Common DealerOn API patterns
        self.api_patterns = [
            "/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_ALL:inventory-data-bus1/getInventory",
            "/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO:inventory-data-bus1/getInventory", 
            "/inventory/api/search",
            "/api/inventory/search",
            "/inventory-api/search"
        ]
    
    def discover_inventory_endpoint(self) -> Optional[str]:
        """
        Discover the correct inventory API endpoint for this dealership
        
        Returns:
            Working endpoint URL or None if none found
        """
        
        for pattern in self.api_patterns:
            endpoint = f"{self.base_url}{pattern}"
            
            self.logger.info(f"🔍 Testing DealerOn endpoint: {endpoint}")
            
            # Test with minimal parameters
            test_params = {
                'start': 0,
                'count': 1
            }
            
            result = self.robust_api_call(
                url=endpoint,
                method="GET",
                params=test_params,
                timeout=15,
                max_retries=1
            )
            
            if result:
                self.logger.info(f"✅ Working DealerOn endpoint found: {endpoint}")
                return endpoint
            else:
                self.logger.warning(f"⚠️ DealerOn endpoint failed: {endpoint}")
        
        self.logger.error("❌ No working DealerOn endpoints found")
        return None
    
    def get_inventory_with_discovery(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get inventory data with automatic endpoint discovery
        
        Args:
            params: Search parameters
            
        Returns:
            Inventory data or None if discovery fails
        """
        
        endpoint = self.discover_inventory_endpoint()
        if not endpoint:
            return None
        
        return self.robust_api_call(
            url=endpoint,
            method="GET",
            params=params,
            timeout=30,
            max_retries=3
        )


# Utility functions for backward compatibility
def create_algolia_handler(app_id: str, api_key: str) -> AlgoliaAPIHandler:
    """Create an Algolia API handler"""
    return AlgoliaAPIHandler(app_id, api_key)

def create_dealeron_handler(base_url: str) -> DealerOnAPIHandler:
    """Create a DealerOn API handler"""
    return DealerOnAPIHandler(base_url)

def test_network_connectivity(urls: List[str]) -> Dict[str, bool]:
    """Test connectivity to multiple URLs"""
    handler = NetworkHandler()
    return handler.test_connectivity(urls)