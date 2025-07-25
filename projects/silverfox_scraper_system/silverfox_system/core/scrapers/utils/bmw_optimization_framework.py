#!/usr/bin/env python3
"""
BMW Optimization Framework
Extends Ranch Mirage optimization framework for BMW dealership scrapers
Provides BMW-specific anti-bot protection and performance optimization
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import base Ranch Mirage optimization framework
try:
    from ranch_mirage_antibot_utils import (
        RanchMirageOptimizationFramework,
        RotatingUserAgent,
        LuxuryDealershipTimingPatterns,
        EnhancedChromeSetup
    )
except ImportError:
    from utils.ranch_mirage_antibot_utils import (
        RanchMirageOptimizationFramework,
        RotatingUserAgent,
        LuxuryDealershipTimingPatterns,
        EnhancedChromeSetup
    )

class BMWDealershipTimingPatterns(LuxuryDealershipTimingPatterns):
    """BMW-specific timing patterns extending luxury dealership patterns"""
    
    def __init__(self, dealership_type: str = "luxury"):
        # BMW dealerships typically use "luxury" tier but can be customized
        super().__init__(dealership_type)
        self.bmw_specific_adjustments = True
        
    def _get_base_delays(self) -> Dict[str, tuple]:
        """BMW-optimized base delays"""
        
        # BMW dealerships often use Algolia API, so optimize for API-heavy usage
        base_delays = super()._get_base_delays()
        
        # Adjust for BMW-specific characteristics
        if self.dealership_type == "luxury":
            # BMW dealerships - slightly more aggressive than ultra-luxury but respectful
            base_delays.update({
                "api_request": (2.0, 4.0),      # Optimized for Algolia API
                "algolia_query": (1.5, 3.0),    # Specific for Algolia searches
                "pagination": (2.0, 4.0),       # Between API pages
                "vehicle_type_switch": (3.0, 6.0),  # Between new/used/certified
            })
        
        return base_delays
    
    def get_algolia_request_delay(self) -> float:
        """Get delay specifically for Algolia API requests"""
        base_delay = random.uniform(*self._get_base_delays()["algolia_query"])
        return self._apply_variance(base_delay)
    
    def get_vehicle_type_delay(self) -> float:
        """Get delay between scraping different vehicle types (new/used/certified)"""
        base_delay = random.uniform(*self._get_base_delays()["vehicle_type_switch"])
        return self._apply_variance(base_delay)

class BMWUserAgent(RotatingUserAgent):
    """BMW-optimized user agents"""
    
    def __init__(self):
        super().__init__()
        
        # Add BMW-specific user agents optimized for automotive sites
        self.bmw_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        
        # Combine with base agents for variety
        self.user_agents = self.bmw_agents + self.user_agents[:3]  # Add some base ones
        
    def get_bmw_optimized_agent(self) -> str:
        """Get a user agent specifically optimized for BMW automotive sites"""
        return random.choice(self.bmw_agents)

class BMWChromeSetup(EnhancedChromeSetup):
    """BMW-optimized Chrome setup"""
    
    def __init__(self, stealth_level: str = "standard"):
        super().__init__(stealth_level)
        
    def get_bmw_chrome_options(self):
        """Get Chrome options optimized for BMW dealership sites"""
        options = super().get_chrome_options("standard")
        
        # BMW-specific optimizations
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Optimize for Algolia-heavy sites
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-threaded-scrolling')
        
        # BMW dealership user agent
        user_agent = BMWUserAgent().get_bmw_optimized_agent()
        options.add_argument(f'--user-agent={user_agent}')
        
        return options

class BMWOptimizationFramework(RanchMirageOptimizationFramework):
    """
    BMW-specific optimization framework
    Extends Ranch Mirage framework with BMW dealership optimizations
    """
    
    def __init__(self, dealership_type: str = "luxury", dealership_name: str = "BMW Dealership"):
        # Initialize with BMW-specific components
        self.dealership_name = dealership_name
        self.dealership_type = dealership_type
        self.framework_type = "BMW"
        
        # BMW-specific managers
        self.user_agent_manager = BMWUserAgent()
        self.timing = BMWDealershipTimingPatterns(dealership_type)
        self.chrome_setup = BMWChromeSetup("standard")
        
        # Optimization stats
        self.stats = {
            'api_requests': 0,
            'algolia_queries': 0,
            'vehicle_type_switches': 0,
            'chrome_fallbacks': 0,
            'total_delays': 0.0,
            'optimization_start': datetime.now()
        }
        
        self.logger = logging.getLogger(f"BMWOptimization.{dealership_name}")
        self.logger.info(f"BMW Optimization Framework initialized for {dealership_name} ({dealership_type})")
    
    def apply_algolia_optimization(self, query_type: str = "search") -> None:
        """Apply optimization specifically for Algolia API requests"""
        delay = self.timing.get_algolia_request_delay()
        
        self.logger.debug(f"Applying Algolia optimization: {delay:.2f}s delay for {query_type}")
        time.sleep(delay)
        
        self.stats['algolia_queries'] += 1
        self.stats['total_delays'] += delay
    
    def apply_vehicle_type_optimization(self) -> None:
        """Apply optimization when switching between vehicle types (new/used/certified)"""
        delay = self.timing.get_vehicle_type_delay()
        
        self.logger.debug(f"Applying vehicle type switch optimization: {delay:.2f}s delay")
        time.sleep(delay)
        
        self.stats['vehicle_type_switches'] += 1
        self.stats['total_delays'] += delay
    
    def get_optimized_chrome_driver(self):
        """Get Chrome driver optimized for BMW dealership sites"""
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            options = self.chrome_setup.get_bmw_chrome_options()
            
            driver = webdriver.Chrome(options=options)
            
            # BMW-specific anti-detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array")
            driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise")
            driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol")
            
            # BMW dealership optimized timeouts
            driver.set_page_load_timeout(45)  # BMW sites can be slower
            driver.implicitly_wait(15)
            
            self.stats['chrome_fallbacks'] += 1
            self.logger.info("BMW-optimized Chrome driver created successfully")
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create BMW-optimized Chrome driver: {str(e)}")
            raise
    
    def apply_request_optimization(self, request_type: str = "api") -> None:
        """Apply optimization for different types of requests"""
        
        if request_type == "algolia":
            self.apply_algolia_optimization()
        elif request_type == "vehicle_type":
            self.apply_vehicle_type_optimization()
        else:
            # Default to parent implementation
            super().apply_request_optimization(request_type)
            self.stats['api_requests'] += 1
    
    def get_bmw_headers(self) -> Dict[str, str]:
        """Get headers optimized for BMW dealership APIs"""
        
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': self.user_agent_manager.get_bmw_optimized_agent(),
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        }
    
    def log_optimization_stats(self) -> None:
        """Log BMW optimization statistics"""
        
        runtime = datetime.now() - self.stats['optimization_start']
        
        self.logger.info("=" * 60)
        self.logger.info(f"BMW OPTIMIZATION STATS - {self.dealership_name}")
        self.logger.info("=" * 60)
        self.logger.info(f"Framework Type: BMW ({self.dealership_type})")
        self.logger.info(f"Runtime: {runtime}")
        self.logger.info(f"API Requests: {self.stats['api_requests']}")
        self.logger.info(f"Algolia Queries: {self.stats['algolia_queries']}")
        self.logger.info(f"Vehicle Type Switches: {self.stats['vehicle_type_switches']}")
        self.logger.info(f"Chrome Fallbacks: {self.stats['chrome_fallbacks']}")
        self.logger.info(f"Total Delay Time: {self.stats['total_delays']:.2f}s")
        
        if self.stats['api_requests'] > 0:
            avg_delay = self.stats['total_delays'] / (self.stats['api_requests'] + self.stats['algolia_queries'])
            self.logger.info(f"Average Delay: {avg_delay:.2f}s per request")
        
        self.logger.info("=" * 60)

# Factory functions for different BMW dealership types

def create_bmw_optimizer(dealership_name: str = "BMW Dealership", dealership_type: str = "luxury") -> BMWOptimizationFramework:
    """Create BMW optimization framework for standard BMW dealerships"""
    return BMWOptimizationFramework(dealership_type, dealership_name)

def create_bmw_west_st_louis_optimizer() -> BMWOptimizationFramework:
    """Create optimization framework specifically for BMW of West St Louis"""
    return BMWOptimizationFramework("luxury", "BMW of West St Louis")

def create_bmw_premium_optimizer(dealership_name: str) -> BMWOptimizationFramework:
    """Create optimization framework for premium BMW dealerships"""
    return BMWOptimizationFramework("supercar", dealership_name)

def create_bmw_m_series_optimizer(dealership_name: str) -> BMWOptimizationFramework:
    """Create optimization framework for BMW M-Series specialized dealerships"""
    return BMWOptimizationFramework("ultra_luxury", dealership_name)

# Compatibility with existing Ranch Mirage framework
def create_bmw_luxury_optimizer() -> BMWOptimizationFramework:
    """Create BMW optimization with luxury tier settings"""
    return create_bmw_optimizer("BMW Dealership", "luxury")