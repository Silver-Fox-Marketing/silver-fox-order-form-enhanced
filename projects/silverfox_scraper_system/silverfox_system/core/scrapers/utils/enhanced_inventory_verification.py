#!/usr/bin/env python3
"""
Enhanced Inventory Verification System
Ensures accurate on-lot inventory scraping with correct counts across all dealership types
Validates against multiple sources and provides comprehensive inventory analysis
"""

import logging
import time
import requests
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Import optimization frameworks for cross-verification
try:
    from multi_dealership_optimization_framework import (
        MultiDealershipOptimizationFramework,
        DealershipGroup,
        DealershipTier,
        DealershipPlatform
    )
except ImportError:
    from utils.multi_dealership_optimization_framework import (
        MultiDealershipOptimizationFramework,
        DealershipGroup,
        DealershipTier,
        DealershipPlatform
    )

class InventoryStatus(Enum):
    """Inventory status enumeration"""
    AVAILABLE = "available"
    SOLD = "sold"
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

class VerificationMethod(Enum):
    """Inventory verification method enumeration"""
    API_COUNT = "api_count"
    WEB_SCRAPE = "web_scrape"
    SITEMAP_ANALYSIS = "sitemap_analysis"
    RSS_FEED = "rss_feed"
    DIRECT_QUERY = "direct_query"
    CROSS_REFERENCE = "cross_reference"

@dataclass
class InventoryCount:
    """Structured inventory count data"""
    total: int
    new: int = 0
    used: int = 0
    certified: int = 0
    available: int = 0
    sold: int = 0
    method: VerificationMethod = VerificationMethod.API_COUNT
    timestamp: datetime = None
    source_url: str = ""
    confidence: float = 1.0  # 0.0 to 1.0

@dataclass
class VehicleValidation:
    """Vehicle validation data"""
    vin: str
    stock_number: str
    make: str
    model: str
    year: int
    status: InventoryStatus
    price: Optional[int]
    days_on_lot: Optional[int]
    last_updated: datetime
    verification_sources: List[str]
    confidence_score: float

class EnhancedInventoryVerificationSystem:
    """
    Enhanced inventory verification system that ensures accurate inventory counts
    and validates against multiple sources to prevent missing or duplicate vehicles
    """
    
    def __init__(self, 
                 dealership_name: str,
                 dealership_config: Dict[str, Any],
                 optimizer: Optional[MultiDealershipOptimizationFramework] = None):
        
        self.dealership_name = dealership_name
        self.dealership_config = dealership_config
        self.optimizer = optimizer
        self.logger = logging.getLogger(f"EnhancedInventoryVerification.{dealership_name}")
        
        # Verification settings
        self.verification_threshold = 0.95  # 95% confidence required
        self.max_discrepancy_percentage = 5.0  # Allow 5% difference between sources
        self.verification_timeout = 300  # 5 minute timeout for verification
        
        # Inventory tracking
        self.inventory_counts = {}
        self.verified_vehicles = {}
        self.verification_history = []
        self.discrepancies = []
        
        # Initialize session for verification requests
        self.verification_session = requests.Session()
        if optimizer:
            self.verification_session.headers.update(optimizer.get_optimized_headers())
    
    def verify_inventory_completeness(self, 
                                    scraped_vehicles: List[Dict[str, Any]],
                                    enable_cross_verification: bool = True) -> Dict[str, Any]:
        """
        Comprehensive inventory verification against multiple sources
        Returns verification report with confidence scores and recommendations
        """
        
        self.logger.info(f"🔍 Starting enhanced inventory verification for {self.dealership_name}")
        self.logger.info(f"   Scraped vehicles to verify: {len(scraped_vehicles)}")
        
        verification_start = time.time()
        verification_report = {
            'dealership': self.dealership_name,
            'scraped_count': len(scraped_vehicles),
            'verification_methods': [],
            'inventory_counts': {},
            'vehicle_validations': [],
            'discrepancies': [],
            'confidence_score': 0.0,
            'recommendations': [],
            'verification_duration': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Method 1: API Count Verification
            api_count = self._verify_via_api_count()
            if api_count:
                verification_report['inventory_counts']['api'] = api_count.__dict__
                verification_report['verification_methods'].append('api_count')
            
            # Method 2: Website Count Verification  
            if enable_cross_verification:
                web_count = self._verify_via_website_count()
                if web_count:
                    verification_report['inventory_counts']['website'] = web_count.__dict__
                    verification_report['verification_methods'].append('web_scrape')
            
            # Method 3: Sitemap Analysis
            if enable_cross_verification:
                sitemap_count = self._verify_via_sitemap_analysis()
                if sitemap_count:
                    verification_report['inventory_counts']['sitemap'] = sitemap_count.__dict__
                    verification_report['verification_methods'].append('sitemap_analysis')
            
            # Method 4: Individual Vehicle Validation
            vehicle_validations = self._validate_individual_vehicles(scraped_vehicles)
            verification_report['vehicle_validations'] = [v.__dict__ for v in vehicle_validations]
            
            # Method 5: Cross-Reference Analysis
            if enable_cross_verification and len(verification_report['inventory_counts']) > 1:
                cross_ref_analysis = self._cross_reference_counts(verification_report['inventory_counts'])
                verification_report['cross_reference'] = cross_ref_analysis
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(verification_report)
            verification_report['confidence_score'] = confidence_score
            
            # Generate recommendations
            recommendations = self._generate_recommendations(verification_report)
            verification_report['recommendations'] = recommendations
            
            # Identify discrepancies
            discrepancies = self._identify_discrepancies(verification_report)
            verification_report['discrepancies'] = discrepancies
            
        except Exception as e:
            self.logger.error(f"❌ Inventory verification failed: {str(e)}")
            verification_report['error'] = str(e)
            verification_report['confidence_score'] = 0.0
        
        verification_report['verification_duration'] = time.time() - verification_start
        
        # Log summary
        self._log_verification_summary(verification_report)
        
        return verification_report
    
    def _verify_via_api_count(self) -> Optional[InventoryCount]:
        """Verify inventory count via dealership API"""
        
        try:
            base_url = self.dealership_config.get('base_url', '')
            if not base_url:
                return None
            
            # Try common API endpoints for inventory counts
            api_endpoints = [
                f"{base_url}/api/inventory/count",
                f"{base_url}/api/vehicles/count", 
                f"{base_url}/inventory/api/count",
                f"{base_url}/searchall.aspx",  # DealerOn
                f"{base_url}/api/vhcliaa/vehicle-pages"  # DealerOn API
            ]
            
            for endpoint in api_endpoints:
                try:
                    if self.optimizer:
                        self.optimizer.apply_request_optimization("api")
                    
                    response = self.verification_session.get(endpoint, timeout=30)
                    
                    if response.status_code == 200:
                        # Try to extract count from response
                        count_data = self._extract_count_from_response(response)
                        if count_data:
                            self.logger.info(f"✅ API count verification successful: {count_data.total} vehicles")
                            return count_data
                        
                except requests.RequestException:
                    continue
            
            self.logger.warning("⚠️ API count verification not available")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ API count verification failed: {str(e)}")
            return None
    
    def _verify_via_website_count(self) -> Optional[InventoryCount]:
        """Verify inventory count by analyzing the dealership website"""
        
        try:
            base_url = self.dealership_config.get('base_url', '')
            if not base_url:
                return None
            
            # Common pages that might show inventory counts
            count_pages = [
                f"{base_url}/inventory",
                f"{base_url}/vehicles",
                f"{base_url}/new-inventory",
                f"{base_url}/used-inventory",
                f"{base_url}/certified-inventory",
                f"{base_url}"  # Home page might have counts
            ]
            
            total_found = 0
            new_count = 0
            used_count = 0
            certified_count = 0
            
            for page_url in count_pages:
                try:
                    if self.optimizer:
                        self.optimizer.apply_request_optimization("page_load")
                    
                    response = self.verification_session.get(page_url, timeout=30)
                    
                    if response.status_code == 200:
                        # Extract counts from page content
                        page_counts = self._extract_counts_from_html(response.text)
                        
                        if page_counts['total'] > total_found:
                            total_found = page_counts['total']
                        if page_counts['new'] > new_count:
                            new_count = page_counts['new']
                        if page_counts['used'] > used_count:
                            used_count = page_counts['used']
                        if page_counts['certified'] > certified_count:
                            certified_count = page_counts['certified']
                        
                except requests.RequestException:
                    continue
            
            if total_found > 0:
                count_data = InventoryCount(
                    total=total_found,
                    new=new_count,
                    used=used_count,
                    certified=certified_count,
                    method=VerificationMethod.WEB_SCRAPE,
                    timestamp=datetime.now(),
                    source_url=base_url,
                    confidence=0.8  # Slightly lower confidence for web scraping
                )
                
                self.logger.info(f"✅ Website count verification successful: {total_found} vehicles")
                return count_data
            
            self.logger.warning("⚠️ Website count verification found no results")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Website count verification failed: {str(e)}")
            return None
    
    def _verify_via_sitemap_analysis(self) -> Optional[InventoryCount]:
        """Verify inventory count by analyzing the dealership sitemap"""
        
        try:
            base_url = self.dealership_config.get('base_url', '')
            if not base_url:
                return None
            
            # Common sitemap locations
            sitemap_urls = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/vehicles-sitemap.xml",
                f"{base_url}/inventory-sitemap.xml"
            ]
            
            vehicle_urls = set()
            
            for sitemap_url in sitemap_urls:
                try:
                    response = self.verification_session.get(sitemap_url, timeout=30)
                    
                    if response.status_code == 200:
                        # Extract vehicle URLs from sitemap
                        urls = self._extract_vehicle_urls_from_sitemap(response.text)
                        vehicle_urls.update(urls)
                        
                except requests.RequestException:
                    continue
            
            if vehicle_urls:
                count_data = InventoryCount(
                    total=len(vehicle_urls),
                    method=VerificationMethod.SITEMAP_ANALYSIS,
                    timestamp=datetime.now(),
                    source_url=f"{base_url}/sitemap.xml",
                    confidence=0.9  # High confidence for sitemap data
                )
                
                self.logger.info(f"✅ Sitemap analysis successful: {len(vehicle_urls)} vehicle URLs found")
                return count_data
            
            self.logger.warning("⚠️ Sitemap analysis found no vehicle URLs")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Sitemap analysis failed: {str(e)}")
            return None
    
    def _validate_individual_vehicles(self, vehicles: List[Dict[str, Any]]) -> List[VehicleValidation]:
        """Validate individual vehicles against dealership sources"""
        
        validations = []
        
        for vehicle in vehicles[:10]:  # Limit to first 10 for performance
            try:
                validation = self._validate_single_vehicle(vehicle)
                if validation:
                    validations.append(validation)
            except Exception as e:
                self.logger.warning(f"Vehicle validation failed for VIN {vehicle.get('vin', 'Unknown')}: {str(e)}")
        
        return validations
    
    def _validate_single_vehicle(self, vehicle: Dict[str, Any]) -> Optional[VehicleValidation]:
        """Validate a single vehicle against dealership sources"""
        
        vin = vehicle.get('vin', '')
        stock_number = vehicle.get('stock_number', '')
        
        if not vin and not stock_number:
            return None
        
        try:
            # Try to verify vehicle exists on dealership website
            base_url = self.dealership_config.get('base_url', '')
            verification_sources = []
            confidence_score = 0.5  # Base confidence
            
            # Check for vehicle detail page
            if vin:
                vehicle_url = f"{base_url}/vehicle/{vin}"
                if self._check_vehicle_url_exists(vehicle_url):
                    verification_sources.append(f"VDP:{vehicle_url}")
                    confidence_score += 0.3
            
            if stock_number:
                stock_url = f"{base_url}/vehicle/stock/{stock_number}"
                if self._check_vehicle_url_exists(stock_url):
                    verification_sources.append(f"Stock:{stock_url}")
                    confidence_score += 0.2
            
            # Determine status
            status = InventoryStatus.AVAILABLE
            if vehicle.get('original_status', '').lower() in ['sold', 'unavailable']:
                status = InventoryStatus.SOLD
            
            validation = VehicleValidation(
                vin=vin,
                stock_number=stock_number,
                make=vehicle.get('make', ''),
                model=vehicle.get('model', ''),
                year=vehicle.get('year', 0),
                status=status,
                price=vehicle.get('price'),
                days_on_lot=None,  # Could be calculated if date_in_stock available
                last_updated=datetime.now(),
                verification_sources=verification_sources,
                confidence_score=min(1.0, confidence_score)
            )
            
            return validation
            
        except Exception as e:
            self.logger.warning(f"Single vehicle validation failed: {str(e)}")
            return None
    
    def _check_vehicle_url_exists(self, url: str) -> bool:
        """Check if a vehicle URL exists and is accessible"""
        
        try:
            response = self.verification_session.head(url, timeout=10)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def _extract_count_from_response(self, response: requests.Response) -> Optional[InventoryCount]:
        """Extract inventory count from API response"""
        
        try:
            # Try JSON response first
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                
                # Common patterns for count in JSON responses
                count_fields = ['total', 'count', 'totalCount', 'total_count', 'vehicleCount']
                
                for field in count_fields:
                    if field in data:
                        total = int(data[field])
                        
                        return InventoryCount(
                            total=total,
                            new=data.get('new_count', 0),
                            used=data.get('used_count', 0),
                            certified=data.get('certified_count', 0),
                            method=VerificationMethod.API_COUNT,
                            timestamp=datetime.now(),
                            confidence=1.0
                        )
                
                # Check for nested structures (like DealerOn API)
                if 'VehiclesModel' in data:
                    vehicles_model = data['VehiclesModel']
                    if 'Paging' in vehicles_model:
                        paging = vehicles_model['Paging']
                        if 'PaginationDataModel' in paging:
                            pagination = paging['PaginationDataModel']
                            total = pagination.get('TotalCount', 0)
                            
                            if total > 0:
                                return InventoryCount(
                                    total=total,
                                    method=VerificationMethod.API_COUNT,
                                    timestamp=datetime.now(),
                                    confidence=1.0
                                )
            
            # Try extracting from HTML response
            if 'text/html' in response.headers.get('content-type', ''):
                counts = self._extract_counts_from_html(response.text)
                if counts['total'] > 0:
                    return InventoryCount(
                        total=counts['total'],
                        new=counts['new'],
                        used=counts['used'],
                        certified=counts['certified'],
                        method=VerificationMethod.DIRECT_QUERY,
                        timestamp=datetime.now(),
                        confidence=0.8
                    )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract count from response: {str(e)}")
            return None
    
    def _extract_counts_from_html(self, html_content: str) -> Dict[str, int]:
        """Extract inventory counts from HTML content"""
        
        counts = {'total': 0, 'new': 0, 'used': 0, 'certified': 0}
        
        try:
            # Common patterns for inventory counts in HTML
            patterns = [
                r'(\d+)\s*(?:vehicles?|cars?|units?)\s*(?:in\s*stock|available|inventory)',
                r'(?:showing|found|total).*?(\d+)\s*(?:vehicles?|results?)',
                r'inventory[^>]*>.*?(\d+)',
                r'(\d+)\s*(?:new|used|certified)\s*(?:vehicles?|cars?)',
                r'data-count=["\'](\d+)["\']',
                r'count["\']:\s*(\d+)',
                r'total["\']:\s*(\d+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    try:
                        count = int(match)
                        if count > counts['total']:
                            counts['total'] = count
                    except ValueError:
                        continue
            
            # Look for specific vehicle type counts
            new_patterns = [r'(\d+)\s*new\s*(?:vehicles?|cars?)', r'new[^>]*>.*?(\d+)']
            used_patterns = [r'(\d+)\s*used\s*(?:vehicles?|cars?)', r'used[^>]*>.*?(\d+)']
            certified_patterns = [r'(\d+)\s*certified\s*(?:vehicles?|cars?)', r'certified[^>]*>.*?(\d+)']
            
            for pattern in new_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    try:
                        count = int(match)
                        if count > counts['new']:
                            counts['new'] = count
                    except ValueError:
                        continue
            
            for pattern in used_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    try:
                        count = int(match)
                        if count > counts['used']:
                            counts['used'] = count
                    except ValueError:
                        continue
            
            for pattern in certified_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    try:
                        count = int(match)
                        if count > counts['certified']:
                            counts['certified'] = count
                    except ValueError:
                        continue
            
        except Exception as e:
            self.logger.warning(f"Failed to extract counts from HTML: {str(e)}")
        
        return counts
    
    def _extract_vehicle_urls_from_sitemap(self, sitemap_content: str) -> Set[str]:
        """Extract vehicle URLs from sitemap XML"""
        
        vehicle_urls = set()
        
        try:
            # Common patterns for vehicle URLs in sitemaps
            url_patterns = [
                r'<loc>(.*?/vehicle/[^<]+)</loc>',
                r'<loc>(.*?/inventory/[^<]+)</loc>',
                r'<loc>(.*?/auto/[^<]+)</loc>',
                r'<loc>(.*?/vdp/[^<]+)</loc>'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, sitemap_content, re.IGNORECASE)
                vehicle_urls.update(matches)
            
        except Exception as e:
            self.logger.warning(f"Failed to extract URLs from sitemap: {str(e)}")
        
        return vehicle_urls
    
    def _cross_reference_counts(self, inventory_counts: Dict[str, Dict]) -> Dict[str, Any]:
        """Cross-reference inventory counts from different sources"""
        
        cross_ref = {
            'sources': list(inventory_counts.keys()),
            'total_counts': {},
            'discrepancies': [],
            'confidence_assessment': 'unknown'
        }
        
        try:
            # Extract total counts from each source
            for source, count_data in inventory_counts.items():
                total = count_data.get('total', 0)
                cross_ref['total_counts'][source] = total
            
            if len(cross_ref['total_counts']) > 1:
                counts = list(cross_ref['total_counts'].values())
                min_count = min(counts)
                max_count = max(counts)
                
                # Calculate discrepancy percentage
                if min_count > 0:
                    discrepancy_pct = ((max_count - min_count) / min_count) * 100
                    
                    if discrepancy_pct <= self.max_discrepancy_percentage:
                        cross_ref['confidence_assessment'] = 'high'
                    elif discrepancy_pct <= self.max_discrepancy_percentage * 2:
                        cross_ref['confidence_assessment'] = 'medium'
                    else:
                        cross_ref['confidence_assessment'] = 'low'
                        
                        # Record significant discrepancies
                        for source, count in cross_ref['total_counts'].items():
                            if abs(count - min_count) / min_count * 100 > self.max_discrepancy_percentage:
                                cross_ref['discrepancies'].append({
                                    'source': source,
                                    'count': count,
                                    'expected_range': f"{min_count}-{max_count}",
                                    'discrepancy_pct': abs(count - min_count) / min_count * 100
                                })
            
        except Exception as e:
            self.logger.warning(f"Cross-reference analysis failed: {str(e)}")
        
        return cross_ref
    
    def _calculate_confidence_score(self, verification_report: Dict[str, Any]) -> float:
        """Calculate overall confidence score for inventory verification"""
        
        try:
            base_score = 0.5  # Start with 50% confidence
            
            # Add points for each verification method
            method_weights = {
                'api_count': 0.3,
                'web_scrape': 0.2,
                'sitemap_analysis': 0.25,
                'cross_reference': 0.15
            }
            
            for method in verification_report.get('verification_methods', []):
                if method in method_weights:
                    base_score += method_weights[method]
            
            # Adjust based on cross-reference analysis
            if 'cross_reference' in verification_report:
                cross_ref = verification_report['cross_reference']
                confidence_assessment = cross_ref.get('confidence_assessment', 'unknown')
                
                if confidence_assessment == 'high':
                    base_score += 0.1
                elif confidence_assessment == 'low':
                    base_score -= 0.15
            
            # Adjust based on individual vehicle validations
            vehicle_validations = verification_report.get('vehicle_validations', [])
            if vehicle_validations:
                avg_vehicle_confidence = sum(v.get('confidence_score', 0) for v in vehicle_validations) / len(vehicle_validations)
                base_score = (base_score + avg_vehicle_confidence) / 2
            
            return min(1.0, max(0.0, base_score))
            
        except Exception as e:
            self.logger.warning(f"Confidence score calculation failed: {str(e)}")
            return 0.5
    
    def _generate_recommendations(self, verification_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results"""
        
        recommendations = []
        
        try:
            confidence_score = verification_report.get('confidence_score', 0.0)
            scraped_count = verification_report.get('scraped_count', 0)
            
            # Confidence-based recommendations
            if confidence_score < 0.6:
                recommendations.append("⚠️ Low confidence score - consider manual verification of inventory counts")
            
            if confidence_score < 0.4:
                recommendations.append("🚨 Very low confidence - investigate scraper accuracy and website changes")
            
            # Count-based recommendations
            if scraped_count == 0:
                recommendations.append("❌ No vehicles scraped - check scraper functionality and website availability")
            
            elif scraped_count < 5:
                recommendations.append("⚠️ Very low vehicle count - verify dealership has active inventory")
            
            # Cross-reference recommendations
            if 'cross_reference' in verification_report:
                cross_ref = verification_report['cross_reference']
                if cross_ref.get('confidence_assessment') == 'low':
                    recommendations.append("📊 Significant discrepancies between sources - investigate data accuracy")
            
            # Method-specific recommendations
            verification_methods = verification_report.get('verification_methods', [])
            
            if len(verification_methods) < 2:
                recommendations.append("🔍 Enable cross-verification for better accuracy assessment")
            
            if 'api_count' not in verification_methods:
                recommendations.append("🔌 API count verification unavailable - may indicate API changes or restrictions")
            
            # Vehicle validation recommendations
            vehicle_validations = verification_report.get('vehicle_validations', [])
            if vehicle_validations:
                low_confidence_vehicles = [v for v in vehicle_validations if v.get('confidence_score', 0) < 0.5]
                if low_confidence_vehicles:
                    recommendations.append(f"🚗 {len(low_confidence_vehicles)} vehicles have low validation confidence")
            
            # Timing recommendations
            verification_duration = verification_report.get('verification_duration', 0)
            if verification_duration > 180:  # 3 minutes
                recommendations.append("⏱️ Verification taking longer than expected - consider optimization")
            
            if not recommendations:
                recommendations.append("✅ Inventory verification looks good - no issues detected")
            
        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {str(e)}")
            recommendations.append("⚠️ Unable to generate recommendations due to analysis error")
        
        return recommendations
    
    def _identify_discrepancies(self, verification_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify and categorize inventory discrepancies"""
        
        discrepancies = []
        
        try:
            inventory_counts = verification_report.get('inventory_counts', {})
            scraped_count = verification_report.get('scraped_count', 0)
            
            # Compare scraped count with verification sources
            for source, count_data in inventory_counts.items():
                source_total = count_data.get('total', 0)
                
                if source_total > 0:
                    difference = abs(scraped_count - source_total)
                    difference_pct = (difference / source_total) * 100
                    
                    if difference_pct > self.max_discrepancy_percentage:
                        discrepancies.append({
                            'type': 'count_mismatch',
                            'source': source,
                            'scraped_count': scraped_count,
                            'source_count': source_total,
                            'difference': difference,
                            'difference_percentage': difference_pct,
                            'severity': 'high' if difference_pct > 20 else 'medium'
                        })
            
            # Check for cross-reference discrepancies
            if 'cross_reference' in verification_report:
                cross_ref_discrepancies = verification_report['cross_reference'].get('discrepancies', [])
                for disc in cross_ref_discrepancies:
                    discrepancies.append({
                        'type': 'cross_reference_mismatch',
                        **disc,
                        'severity': 'high' if disc.get('discrepancy_pct', 0) > 25 else 'medium'
                    })
            
            # Check for vehicle validation discrepancies
            vehicle_validations = verification_report.get('vehicle_validations', [])
            low_confidence_count = sum(1 for v in vehicle_validations if v.get('confidence_score', 0) < 0.5)
            
            if low_confidence_count > len(vehicle_validations) * 0.3:  # More than 30% low confidence
                discrepancies.append({
                    'type': 'vehicle_validation_low_confidence',
                    'low_confidence_count': low_confidence_count,
                    'total_validated': len(vehicle_validations),
                    'percentage': (low_confidence_count / len(vehicle_validations)) * 100,
                    'severity': 'medium'
                })
            
        except Exception as e:
            self.logger.warning(f"Discrepancy identification failed: {str(e)}")
        
        return discrepancies
    
    def _log_verification_summary(self, verification_report: Dict[str, Any]) -> None:
        """Log comprehensive verification summary"""
        
        self.logger.info("=" * 80)
        self.logger.info(f"📊 INVENTORY VERIFICATION SUMMARY - {self.dealership_name}")
        self.logger.info("=" * 80)
        
        # Basic metrics
        scraped_count = verification_report.get('scraped_count', 0)
        confidence_score = verification_report.get('confidence_score', 0.0)
        verification_methods = verification_report.get('verification_methods', [])
        
        self.logger.info(f"Scraped vehicles: {scraped_count}")
        self.logger.info(f"Confidence score: {confidence_score:.2f}")
        self.logger.info(f"Verification methods: {', '.join(verification_methods)}")
        
        # Inventory counts from different sources
        inventory_counts = verification_report.get('inventory_counts', {})
        if inventory_counts:
            self.logger.info("\n📈 INVENTORY COUNTS BY SOURCE:")
            for source, count_data in inventory_counts.items():
                total = count_data.get('total', 0)
                confidence = count_data.get('confidence', 0.0)
                self.logger.info(f"  {source.upper()}: {total} vehicles (confidence: {confidence:.2f})")
        
        # Discrepancies
        discrepancies = verification_report.get('discrepancies', [])
        if discrepancies:
            self.logger.info(f"\n⚠️ DISCREPANCIES FOUND ({len(discrepancies)}):")
            for disc in discrepancies:
                severity = disc.get('severity', 'unknown').upper()
                disc_type = disc.get('type', 'unknown')
                self.logger.info(f"  [{severity}] {disc_type}: {disc}")
        
        # Recommendations
        recommendations = verification_report.get('recommendations', [])
        if recommendations:
            self.logger.info(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                self.logger.info(f"  {rec}")
        
        # Overall assessment
        if confidence_score >= 0.9:
            self.logger.info(f"\n✅ EXCELLENT: High confidence in inventory accuracy")
        elif confidence_score >= 0.7:
            self.logger.info(f"\n👍 GOOD: Reasonable confidence in inventory accuracy")
        elif confidence_score >= 0.5:
            self.logger.info(f"\n⚠️ FAIR: Some concerns about inventory accuracy")
        else:
            self.logger.info(f"\n🚨 POOR: Low confidence in inventory accuracy - investigation needed")
        
        self.logger.info("=" * 80)

# Integration functions for existing scrapers

def enhance_scraper_with_verification(scraper_instance, 
                                    dealership_config: Dict[str, Any],
                                    optimizer: Optional[MultiDealershipOptimizationFramework] = None) -> None:
    """Enhance an existing scraper instance with advanced inventory verification"""
    
    verification_system = EnhancedInventoryVerificationSystem(
        scraper_instance.dealership_name,
        dealership_config,
        optimizer
    )
    
    # Add verification system to scraper
    scraper_instance.enhanced_verification = verification_system
    
    # Add verification method to scraper
    def verify_scraped_inventory(self, vehicles: List[Dict[str, Any]], enable_cross_verification: bool = True) -> Dict[str, Any]:
        return self.enhanced_verification.verify_inventory_completeness(vehicles, enable_cross_verification)
    
    # Bind method to scraper instance
    import types
    scraper_instance.verify_scraped_inventory = types.MethodType(verify_scraped_inventory, scraper_instance)

def create_verification_system(dealership_name: str, 
                             dealership_config: Dict[str, Any],
                             optimizer: Optional[MultiDealershipOptimizationFramework] = None) -> EnhancedInventoryVerificationSystem:
    """Factory function to create verification system"""
    return EnhancedInventoryVerificationSystem(dealership_name, dealership_config, optimizer)