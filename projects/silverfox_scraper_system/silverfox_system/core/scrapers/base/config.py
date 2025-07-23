import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ScraperMode(Enum):
    HEADLESS = "headless"
    VISIBLE = "visible"
    FAST = "fast"

class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"

@dataclass
class ScraperConfig:
    """Configuration class for scraper settings"""
    
    # Browser settings
    mode: ScraperMode = ScraperMode.HEADLESS
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Request settings
    timeout: int = 30
    page_load_timeout: int = 60
    implicit_wait: int = 10
    
    # Rate limiting
    request_delay: float = 1.0
    rate_limit_per_minute: int = 60
    concurrent_workers: int = 3
    
    # Retry settings
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retry_delay: float = 1.0
    
    # Error handling
    ignore_ssl_errors: bool = True
    handle_cloudflare: bool = True
    auto_captcha_solving: bool = False
    
    # Output settings
    output_format: str = "json"
    output_directory: str = "output_data"
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # Conditional rules
    conditional_rules: Dict[str, any] = None
    
    def __post_init__(self):
        if self.conditional_rules is None:
            self.conditional_rules = {}
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)

# Default configurations for different site types
DEALERSHIP_CONFIG = ScraperConfig(
    mode=ScraperMode.HEADLESS,
    timeout=45,
    page_load_timeout=90,
    request_delay=2.0,
    rate_limit_per_minute=30,
    max_retries=5,
    conditional_rules={
        "inventory_selectors": [
            ".vehicle-item",
            ".car-listing",
            ".inventory-item",
            "[data-vehicle-id]"
        ],
        "price_selectors": [
            ".price",
            ".vehicle-price",
            "[data-price]",
            ".msrp"
        ],
        "required_fields": ["make", "model", "year", "price"],
        "skip_if_missing": ["price"],
        "pagination_selectors": [
            ".pagination .next",
            ".next-page",
            "[aria-label='Next']"
        ]
    }
)

GENERAL_CONFIG = ScraperConfig(
    mode=ScraperMode.FAST,
    timeout=20,
    request_delay=0.5,
    rate_limit_per_minute=120,
    max_retries=2
)