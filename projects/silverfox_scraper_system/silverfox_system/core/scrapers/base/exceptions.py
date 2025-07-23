
class ScraperError(Exception):
    """Base exception for scraper errors"""
    pass

class ConfigurationError(ScraperError):
    """Raised when scraper configuration is invalid"""
    pass

class NetworkError(ScraperError):
    """Raised when network-related errors occur"""
    pass

class TimeoutError(ScraperError):
    """Raised when operations timeout"""
    pass

class ParsingError(ScraperError):
    """Raised when data parsing fails"""
    pass

class ValidationError(ScraperError):
    """Raised when scraped data validation fails"""
    pass

class RateLimitError(ScraperError):
    """Raised when rate limits are exceeded"""
    pass

class CaptchaError(ScraperError):
    """Raised when CAPTCHA detection occurs"""
    pass

class CloudflareError(ScraperError):
    """Raised when Cloudflare protection is detected"""
    pass

class ElementNotFoundError(ScraperError):
    """Raised when required elements are not found"""
    pass

class DataIntegrityError(ScraperError):
    """Raised when scraped data fails integrity checks"""
    pass