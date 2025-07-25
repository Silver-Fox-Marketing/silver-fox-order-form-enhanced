"""
Ranch Mirage Anti-Bot Utilities Module
Comprehensive utilities for enhanced anti-bot protection across all indiGO Auto Group luxury dealerships
Following established patterns from working scrapers
"""

import random
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class RotatingUserAgent:
    """Rotating user agent manager for luxury dealership sites"""
    
    def __init__(self):
        self.agents = [
            # Windows Chrome (Latest versions)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            
            # Windows Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            
            # macOS Chrome
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # macOS Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
        ]
        self.current_index = 0
    
    def get_random_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.agents)
    
    def get_rotating_agent(self) -> str:
        """Get next user agent in rotation"""
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent

class LuxuryDealershipTimingPatterns:
    """Advanced timing patterns for luxury dealership anti-bot protection"""
    
    def __init__(self, dealership_type: str = "luxury"):
        self.dealership_type = dealership_type
        self.base_delays = self._get_base_delays()
        self.logger = logging.getLogger(__name__)
    
    def _get_base_delays(self) -> Dict[str, Tuple[float, float]]:
        """Get base delay ranges by dealership type"""
        if self.dealership_type == "ultra_luxury":  # Rolls-Royce
            return {
                "request": (8.0, 15.0),
                "page_load": (15.0, 25.0),
                "element_wait": (3.0, 8.0),
                "retry": (30.0, 60.0)
            }
        elif self.dealership_type == "supercar":  # McLaren
            return {
                "request": (6.0, 12.0),
                "page_load": (12.0, 20.0),
                "element_wait": (2.5, 6.0),
                "retry": (25.0, 45.0)
            }
        else:  # Standard luxury (Jaguar, Land Rover, Aston Martin, Bentley)
            return {
                "request": (4.0, 8.0),
                "page_load": (8.0, 15.0),
                "element_wait": (2.0, 5.0),
                "retry": (20.0, 40.0)
            }
    
    def get_request_delay(self) -> float:
        """Get randomized request delay"""
        min_delay, max_delay = self.base_delays["request"]
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Using request delay: {delay:.2f}s")
        return delay
    
    def get_page_load_delay(self) -> float:
        """Get randomized page load delay"""
        min_delay, max_delay = self.base_delays["page_load"]
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Using page load delay: {delay:.2f}s")
        return delay
    
    def get_element_wait_delay(self) -> float:
        """Get randomized element wait delay"""
        min_delay, max_delay = self.base_delays["element_wait"]
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Using element wait delay: {delay:.2f}s")
        return delay
    
    def get_retry_delay(self) -> float:
        """Get randomized retry delay"""
        min_delay, max_delay = self.base_delays["retry"]
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Using retry delay: {delay:.2f}s")
        return delay
    
    def humanized_sleep(self, base_delay: float, variance: float = 0.3) -> None:
        """Sleep with human-like variance"""
        variance_amount = base_delay * variance
        actual_delay = random.uniform(
            base_delay - variance_amount,
            base_delay + variance_amount
        )
        time.sleep(max(0.1, actual_delay))

class EnhancedChromeSetup:
    """Enhanced Chrome driver setup for luxury dealerships"""
    
    def __init__(self, dealership_type: str = "luxury"):
        self.dealership_type = dealership_type
        self.user_agent_manager = RotatingUserAgent()
        self.timing = LuxuryDealershipTimingPatterns(dealership_type)
        self.logger = logging.getLogger(__name__)
    
    def create_stealth_options(self, user_agent: str = None) -> Options:
        """Create stealth Chrome options optimized for luxury dealerships"""
        
        options = Options()
        
        # Core stealth options
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        # Performance optimizations for luxury sites
        options.add_argument('--disable-images')
        options.add_argument('--disable-css')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-default-apps')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-background-networking')
        options.add_argument('--memory-pressure-off')
        
        # Advanced anti-detection for luxury sites
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth measures for ultra-luxury
        if self.dealership_type in ["ultra_luxury", "supercar"]:
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-field-trial-config')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-prompt-on-repost')
        
        # User agent
        if not user_agent:
            user_agent = self.user_agent_manager.get_random_agent()
        options.add_argument(f'--user-agent={user_agent}')
        
        # Advanced preferences
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,
                "plugins": 2, 
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
                "cookies": 1
            },
            "profile.managed_default_content_settings": {
                "images": 2
            },
            "profile.content_settings.exceptions.automatic_downloads": {
                "*": {"setting": 2}
            }
        }
        
        # Ultra-luxury specific preferences
        if self.dealership_type == "ultra_luxury":
            prefs.update({
                "profile.default_content_settings": {
                    "mouselock": 2,
                    "media_stream": 2,
                    "camera": 2,
                    "microphone": 2
                }
            })
        
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def setup_driver_with_stealth(self, user_agent: str = None) -> webdriver.Chrome:
        """Setup Chrome driver with full stealth configuration"""
        
        options = self.create_stealth_options(user_agent)
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Execute stealth scripts
            self._execute_stealth_scripts(driver)
            
            # Set timeouts based on dealership type
            timeouts = self._get_timeouts()
            driver.set_page_load_timeout(timeouts["page_load"])
            driver.implicitly_wait(timeouts["implicit"])
            
            self.logger.info(f"Enhanced Chrome driver setup successful for {self.dealership_type} dealership")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced Chrome driver: {str(e)}")
            raise
    
    def _execute_stealth_scripts(self, driver: webdriver.Chrome) -> None:
        """Execute JavaScript stealth scripts"""
        
        stealth_scripts = [
            # Hide webdriver property
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # Mock plugins
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            
            # Mock languages
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            
            # Mock permissions
            "Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})",
            
            # Mock connection
            "Object.defineProperty(navigator, 'connection', {get: () => ({effectiveType: '4g', rtt: 50, downlink: 2})})",
            
            # Mock device memory (luxury device simulation)
            "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})",
            
            # Mock hardware concurrency
            "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8})",
        ]
        
        # Ultra-luxury specific scripts
        if self.dealership_type in ["ultra_luxury", "supercar"]:
            stealth_scripts.extend([
                # Mock WebGL
                "const getParameter = WebGLRenderingContext.getParameter; WebGLRenderingContext.prototype.getParameter = function(parameter) { if (parameter === 37445) { return 'Intel Inc.'; } if (parameter === 37446) { return 'Intel(R) HD Graphics 630'; } return getParameter(parameter); }",
                
                # Mock canvas fingerprinting
                "const getContext = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) { if (contextType === '2d') { const context = getContext.call(this, contextType, contextAttributes); const getImageData = context.getImageData; context.getImageData = function(sx, sy, sw, sh) { const imageData = getImageData.call(this, sx, sy, sw, sh); for (let i = 0; i < imageData.data.length; i += 4) { imageData.data[i] = imageData.data[i] + Math.floor(Math.random() * 10) - 5; } return imageData; }; return context; } return getContext.call(this, contextType, contextAttributes); }",
            ])
        
        for script in stealth_scripts:
            try:
                driver.execute_script(script)
            except Exception as e:
                self.logger.warning(f"Failed to execute stealth script: {str(e)}")
    
    def _get_timeouts(self) -> Dict[str, int]:
        """Get timeout configuration based on dealership type"""
        if self.dealership_type == "ultra_luxury":
            return {"page_load": 120, "implicit": 30}
        elif self.dealership_type == "supercar":
            return {"page_load": 90, "implicit": 25}
        else:
            return {"page_load": 60, "implicit": 20}

class ProxyManager:
    """Proxy management for luxury dealership scraping"""
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.logger = logging.getLogger(__name__)
    
    def add_proxy(self, proxy_url: str, username: str = None, password: str = None) -> None:
        """Add a proxy to the rotation"""
        proxy_config = {
            "url": proxy_url,
            "username": username,
            "password": password
        }
        self.proxies.append(proxy_config)
        self.logger.info(f"Added proxy: {proxy_url}")
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def configure_proxy_for_chrome(self, options: Options, proxy_config: Dict[str, str]) -> None:
        """Configure proxy for Chrome options"""
        if proxy_config:
            proxy_url = proxy_config["url"]
            options.add_argument(f'--proxy-server={proxy_url}')
            
            if proxy_config.get("username") and proxy_config.get("password"):
                # Note: For authenticated proxies, additional setup might be needed
                self.logger.info(f"Using authenticated proxy: {proxy_url}")
            else:
                self.logger.info(f"Using proxy: {proxy_url}")

class RequestPatternOptimizer:
    """Optimize request patterns for luxury dealership sites"""
    
    def __init__(self, dealership_type: str = "luxury"):
        self.dealership_type = dealership_type
        self.timing = LuxuryDealershipTimingPatterns(dealership_type)
        self.request_history = []
        self.max_history = 100
        self.logger = logging.getLogger(__name__)
    
    def smart_delay(self, request_type: str = "standard") -> None:
        """Apply smart delay based on request history and type"""
        
        base_delay = self.timing.get_request_delay()
        
        # Adjust based on recent request frequency
        recent_requests = len([r for r in self.request_history[-10:] if time.time() - r < 60])
        if recent_requests > 5:
            base_delay *= 1.5  # Slow down if too many recent requests
            self.logger.debug(f"Increased delay due to recent activity: {base_delay:.2f}s")
        
        # Adjust based on request type
        if request_type == "api":
            base_delay *= 0.8  # API requests can be slightly faster
        elif request_type == "chrome":
            base_delay *= 1.2  # Chrome requests should be slower
        
        self.timing.humanized_sleep(base_delay)
        
        # Record request time
        self.request_history.append(time.time())
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    def should_retry(self, attempt: int, max_attempts: int = 3) -> bool:
        """Determine if should retry based on attempt count and timing"""
        if attempt >= max_attempts:
            return False
        
        # Use exponential backoff with jitter
        retry_delay = self.timing.get_retry_delay() * (2 ** attempt)
        retry_delay += random.uniform(0, retry_delay * 0.1)  # Add jitter
        
        self.logger.info(f"Retrying in {retry_delay:.2f}s (attempt {attempt + 1}/{max_attempts})")
        time.sleep(retry_delay)
        return True

class RanchMirageOptimizationFramework:
    """Main optimization framework for all Ranch Mirage scrapers"""
    
    def __init__(self, dealership_type: str = "luxury"):
        self.dealership_type = dealership_type
        self.user_agent_manager = RotatingUserAgent()
        self.chrome_setup = EnhancedChromeSetup(dealership_type)
        self.proxy_manager = ProxyManager()
        self.request_optimizer = RequestPatternOptimizer(dealership_type)
        self.timing = LuxuryDealershipTimingPatterns(dealership_type)
        self.logger = logging.getLogger(__name__)
    
    def get_optimized_chrome_driver(self, use_proxy: bool = False) -> webdriver.Chrome:
        """Get fully optimized Chrome driver"""
        
        user_agent = self.user_agent_manager.get_rotating_agent()
        self.logger.info(f"Using user agent: {user_agent}")
        
        if use_proxy:
            proxy_config = self.proxy_manager.get_next_proxy()
            if proxy_config:
                options = self.chrome_setup.create_stealth_options(user_agent)
                self.proxy_manager.configure_proxy_for_chrome(options, proxy_config)
                driver = webdriver.Chrome(options=options)
                self.chrome_setup._execute_stealth_scripts(driver)
                return driver
        
        return self.chrome_setup.setup_driver_with_stealth(user_agent)
    
    def apply_request_optimization(self, request_type: str = "standard") -> None:
        """Apply optimized request timing"""
        self.request_optimizer.smart_delay(request_type)
    
    def should_retry_with_optimization(self, attempt: int, max_attempts: int = 3) -> bool:
        """Enhanced retry logic with optimization"""
        return self.request_optimizer.should_retry(attempt, max_attempts)
    
    def get_page_load_delay(self) -> float:
        """Get optimized page load delay"""
        return self.timing.get_page_load_delay()
    
    def get_element_wait_delay(self) -> float:
        """Get optimized element wait delay"""
        return self.timing.get_element_wait_delay()
    
    def log_optimization_stats(self) -> None:
        """Log optimization statistics"""
        recent_requests = len(self.request_optimizer.request_history)
        self.logger.info(f"Optimization stats - Recent requests: {recent_requests}, Dealership type: {self.dealership_type}")

# Factory functions for different dealership types

def create_jaguar_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for Jaguar Rancho Mirage"""
    return RanchMirageOptimizationFramework("luxury")

def create_landrover_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for Land Rover Rancho Mirage"""
    return RanchMirageOptimizationFramework("luxury")

def create_astonmartin_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for Aston Martin Rancho Mirage"""
    return RanchMirageOptimizationFramework("luxury")

def create_bentley_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for Bentley Rancho Mirage"""
    return RanchMirageOptimizationFramework("luxury")

def create_mclaren_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for McLaren Rancho Mirage"""
    return RanchMirageOptimizationFramework("supercar")

def create_rollsroyce_optimizer() -> RanchMirageOptimizationFramework:
    """Create optimizer for Rolls-Royce Motor Cars Rancho Mirage"""
    return RanchMirageOptimizationFramework("ultra_luxury")