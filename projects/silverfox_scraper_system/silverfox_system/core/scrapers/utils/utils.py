import time
import json
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import random

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger("scraper")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep essential punctuation
    text = re.sub(r'[^\w\s\.,\-\$\(\)]', '', text)
    
    return text

def extract_price(text: str) -> Optional[float]:
    """Extract price from text string"""
    if not text:
        return None
    
    # Remove currency symbols and formatting
    price_text = re.sub(r'[^\d\.,]', '', text)
    
    # Handle comma-separated thousands
    price_text = price_text.replace(',', '')
    
    try:
        return float(price_text)
    except (ValueError, TypeError):
        return None

def generate_hash(data: Union[str, Dict]) -> str:
    """Generate hash for data deduplication"""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    
    return hashlib.md5(data_str.encode()).hexdigest()

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalize and join URLs"""
    if base_url and not url.startswith(('http://', 'https://')):
        return urljoin(base_url, url)
    return url

def calculate_delay(attempt: int, base_delay: float = 1.0, strategy: str = "exponential") -> float:
    """Calculate delay for retry attempts"""
    if strategy == "exponential":
        return base_delay * (2 ** attempt) + random.uniform(0, 1)
    elif strategy == "linear":
        return base_delay * attempt + random.uniform(0, 1)
    else:  # fixed
        return base_delay + random.uniform(0, 1)

def is_rate_limited(last_request_time: float, min_delay: float) -> bool:
    """Check if we should apply rate limiting"""
    current_time = time.time()
    return (current_time - last_request_time) < min_delay

def wait_for_rate_limit(last_request_time: float, min_delay: float) -> None:
    """Wait for rate limit if necessary"""
    current_time = time.time()
    elapsed = current_time - last_request_time
    
    if elapsed < min_delay:
        sleep_time = min_delay - elapsed
        time.sleep(sleep_time)

class RateLimiter:
    """Rate limiter for managing request frequency"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits"""
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        return len(self.requests) < self.max_requests
    
    def make_request(self) -> None:
        """Record a request"""
        self.requests.append(time.time())
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded"""
        if not self.can_make_request():
            # Calculate how long to wait
            oldest_request = min(self.requests)
            wait_time = self.time_window - (time.time() - oldest_request)
            if wait_time > 0:
                time.sleep(wait_time + 0.1)  # Small buffer

def save_data(data: Any, filepath: str, format_type: str = "json") -> None:
    """Save data to file in specified format"""
    try:
        if format_type.lower() == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    except Exception as e:
        raise Exception(f"Failed to save data: {str(e)}")

def load_data(filepath: str, format_type: str = "json") -> Any:
    """Load data from file"""
    try:
        if format_type.lower() == "json":
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    except FileNotFoundError:
        return None
    except Exception as e:
        raise Exception(f"Failed to load data: {str(e)}")

def merge_selectors(selectors: List[str], element) -> Optional[Any]:
    """Try multiple selectors and return first match"""
    for selector in selectors:
        try:
            if element.find_element("css selector", selector):
                return element.find_element("css selector", selector)
        except:
            continue
    return None