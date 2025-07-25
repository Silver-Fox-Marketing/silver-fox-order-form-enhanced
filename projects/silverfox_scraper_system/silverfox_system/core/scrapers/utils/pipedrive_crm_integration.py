#!/usr/bin/env python3
"""
PipeDrive CRM Integration Module
Integrates Silver Fox scraper system with PipeDrive CRM for sales team workflow
Manages inventory data, leads, alerts, and competitive insights within PipeDrive
"""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# Import related modules
try:
    from realtime_inventory_alerts import InventoryAlert, AlertType, AlertPriority
    from competitive_pricing_analysis import CompetitivePricingAnalyzer
    from enhanced_inventory_verification import VehicleValidation
except ImportError:
    try:
        from utils.realtime_inventory_alerts import InventoryAlert, AlertType, AlertPriority
        from utils.competitive_pricing_analysis import CompetitivePricingAnalyzer
        from utils.enhanced_inventory_verification import VehicleValidation
    except ImportError:
        # Create mock classes for testing
        class InventoryAlert:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class AlertType:
            NEW_VEHICLE = "new_vehicle"
            PRICE_DROP = "price_drop"
        
        class AlertPriority:
            HIGH = "high"
            MEDIUM = "medium"
        
        class CompetitivePricingAnalyzer:
            def __init__(self, **kwargs):
                pass
        
        class VehicleValidation:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

class PipeDriveObjectType(Enum):
    """PipeDrive object types for integration"""
    DEAL = "deal"
    PERSON = "person"
    ORGANIZATION = "organization"
    ACTIVITY = "activity"
    NOTE = "note"
    PRODUCT = "product"
    PIPELINE = "pipeline"
    STAGE = "stage"

class DealStage(Enum):
    """Deal stages in PipeDrive pipeline"""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class InventoryStatus(Enum):
    """Vehicle inventory status in PipeDrive"""
    AVAILABLE = "available"
    PENDING = "pending"
    SOLD = "sold"
    RESERVED = "reserved"
    IN_TRANSIT = "in_transit"

@dataclass
class PipeDriveConfiguration:
    """PipeDrive CRM configuration"""
    api_token: str
    company_domain: str
    pipeline_id: Optional[int] = None
    stage_mapping: Dict[str, int] = field(default_factory=dict)
    custom_field_mapping: Dict[str, int] = field(default_factory=dict)
    webhook_url: Optional[str] = None
    rate_limit_per_second: float = 10.0  # PipeDrive allows 100 requests per 10 seconds
    timeout: int = 30

@dataclass
class VehicleDeal:
    """Vehicle deal representation in PipeDrive"""
    vin: str
    dealership_name: str
    make: str
    model: str
    year: int
    price: int
    deal_id: Optional[int] = None
    deal_title: str = ""
    stage: DealStage = DealStage.LEAD
    status: InventoryStatus = InventoryStatus.AVAILABLE
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    product_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CompetitorInsight:
    """Competitor pricing insight for PipeDrive"""
    vin: str
    competitor_dealership: str
    our_price: int
    competitor_price: int
    price_advantage: int  # Positive if we're cheaper
    market_position: str
    insight_text: str
    priority: str
    created_at: datetime = field(default_factory=datetime.now)

class PipeDriveCRMIntegration:
    """
    Comprehensive PipeDrive CRM integration for Silver Fox scraper system
    Manages vehicles as deals, tracks inventory changes, and provides sales insights
    """
    
    def __init__(self, config: PipeDriveConfiguration):
        self.config = config
        self.logger = logging.getLogger("PipeDriveCRMIntegration")
        
        # API configuration
        self.base_url = f"https://{config.company_domain}.pipedrive.com/api/v1"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Rate limiting
        self.last_request = 0
        self.request_count = 0
        self.request_window_start = time.time()
        
        # Caching
        self.pipeline_cache = {}
        self.stage_cache = {}
        self.custom_fields_cache = {}
        self.deal_cache = {}
        
        # Integration tracking
        self.sync_history = []
        self.error_log = []
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Setup initial configuration
        self._initialize_pipedrive_setup()
    
    def _initialize_pipedrive_setup(self):
        """Initialize PipeDrive configuration and mappings"""
        
        try:
            self.logger.info("🔧 Initializing PipeDrive CRM integration...")
            
            # Get pipeline information
            self._cache_pipeline_info()
            
            # Get custom fields
            self._cache_custom_fields()
            
            # Verify API connection
            self._verify_api_connection()
            
            self.logger.info("✅ PipeDrive CRM integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ PipeDrive initialization failed: {str(e)}")
            raise
    
    def _verify_api_connection(self) -> bool:
        """Verify API connection and permissions"""
        
        try:
            response = self._make_api_request('GET', '/users/me')
            
            if response and response.get('success'):
                user_data = response.get('data', {})
                self.logger.info(f"✅ Connected to PipeDrive as: {user_data.get('name', 'Unknown')}")
                self.logger.info(f"   Company: {user_data.get('company_name', 'Unknown')}")
                return True
            else:
                self.logger.error("❌ API connection verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API connection verification error: {str(e)}")
            return False
    
    def _cache_pipeline_info(self):
        """Cache pipeline and stage information"""
        
        try:
            # Get pipelines
            pipelines_response = self._make_api_request('GET', '/pipelines')
            if pipelines_response and pipelines_response.get('success'):
                pipelines = pipelines_response.get('data', [])
                
                for pipeline in pipelines:
                    pipeline_id = pipeline['id']
                    self.pipeline_cache[pipeline_id] = pipeline
                    
                    # Cache stages for this pipeline
                    stages_response = self._make_api_request('GET', f'/stages?pipeline_id={pipeline_id}')
                    if stages_response and stages_response.get('success'):
                        stages = stages_response.get('data', [])
                        self.stage_cache[pipeline_id] = {stage['name'].lower(): stage['id'] for stage in stages}
                
                self.logger.info(f"📊 Cached {len(self.pipeline_cache)} pipelines and stages")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cache pipeline info: {str(e)}")
    
    def _cache_custom_fields(self):
        """Cache custom field definitions"""
        
        try:
            # Deal custom fields
            deals_fields_response = self._make_api_request('GET', '/dealFields')
            if deals_fields_response and deals_fields_response.get('success'):
                fields = deals_fields_response.get('data', [])
                
                for field in fields:
                    field_key = field.get('key', '')
                    field_id = field.get('id')
                    self.custom_fields_cache[field_key] = field_id
                
                self.logger.info(f"🔧 Cached {len(self.custom_fields_cache)} custom fields")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cache custom fields: {str(e)}")
    
    def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make rate-limited API request to PipeDrive"""
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add API token to params
            if not params:
                params = {}
            params['api_token'] = self.config.api_token
            
            # Make request
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.config.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data, timeout=self.config.timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, params=params, json=data, timeout=self.config.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=self.config.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API request failed: {method} {endpoint} - {str(e)}")
            self.error_log.append({
                'timestamp': datetime.now(),
                'method': method,
                'endpoint': endpoint,
                'error': str(e)
            })
            return None
        
        except Exception as e:
            self.logger.error(f"❌ Unexpected error in API request: {str(e)}")
            return None
    
    def _apply_rate_limiting(self):
        """Apply rate limiting for PipeDrive API"""
        
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.request_window_start > 10.0:  # 10 second window
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if we need to wait
        if self.request_count >= 100:  # PipeDrive limit: 100 requests per 10 seconds
            sleep_time = 10.0 - (current_time - self.request_window_start)
            if sleep_time > 0:
                self.logger.info(f"⏱️ Rate limit reached, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        # Increment counter
        self.request_count += 1
        self.last_request = current_time
    
    def sync_vehicle_inventory(self, vehicles: List[Dict[str, Any]], dealership_name: str) -> Dict[str, Any]:
        """
        Sync vehicle inventory with PipeDrive as deals/products
        Returns sync report with statistics
        """
        
        self.logger.info(f"🔄 Syncing {len(vehicles)} vehicles from {dealership_name} to PipeDrive...")
        
        sync_report = {
            'dealership': dealership_name,
            'total_vehicles': len(vehicles),
            'deals_created': 0,
            'deals_updated': 0,
            'deals_archived': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': [],
            'sync_duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Get existing deals for this dealership
            existing_deals = self._get_dealership_deals(dealership_name)
            existing_vins = {deal.get('vin', ''): deal for deal in existing_deals}
            
            # Process each vehicle
            for vehicle in vehicles:
                try:
                    vin = vehicle.get('vin', '')
                    if not vin:
                        continue
                    
                    # Check if deal already exists
                    if vin in existing_vins:
                        # Update existing deal
                        success = self._update_vehicle_deal(vehicle, existing_vins[vin])
                        if success:
                            sync_report['deals_updated'] += 1
                    else:
                        # Create new deal
                        deal_id = self._create_vehicle_deal(vehicle, dealership_name)
                        if deal_id:
                            sync_report['deals_created'] += 1
                    
                    # Also create/update as product for inventory tracking
                    product_success = self._sync_vehicle_product(vehicle, dealership_name)
                    if product_success:
                        if vin not in existing_vins:
                            sync_report['products_created'] += 1
                        else:
                            sync_report['products_updated'] += 1
                
                except Exception as e:
                    error_msg = f"Vehicle sync error for VIN {vehicle.get('vin', 'Unknown')}: {str(e)}"
                    self.logger.error(error_msg)
                    sync_report['errors'].append(error_msg)
            
            # Archive deals for vehicles no longer in inventory
            current_vins = {v.get('vin', '') for v in vehicles if v.get('vin')}
            for existing_vin, existing_deal in existing_vins.items():
                if existing_vin not in current_vins:
                    success = self._archive_vehicle_deal(existing_deal)
                    if success:
                        sync_report['deals_archived'] += 1
        
        except Exception as e:
            error_msg = f"Inventory sync failed: {str(e)}"
            self.logger.error(error_msg)
            sync_report['errors'].append(error_msg)
        
        sync_report['sync_duration'] = time.time() - start_time
        
        # Log sync summary
        self._log_sync_summary(sync_report)
        
        # Store sync history
        self.sync_history.append(sync_report)
        
        return sync_report
    
    def _get_dealership_deals(self, dealership_name: str) -> List[Dict[str, Any]]:
        """Get existing deals for a dealership"""
        
        try:
            # Search for deals with dealership name
            params = {
                'term': dealership_name,
                'fields': 'title,custom_fields',
                'limit': 500
            }
            
            response = self._make_api_request('GET', '/deals/search', params=params)
            
            if response and response.get('success'):
                deals = response.get('data', {}).get('items', [])
                
                # Extract deals with VIN information
                dealership_deals = []
                for deal in deals:
                    # Look for VIN in custom fields
                    vin = self._extract_vin_from_deal(deal)
                    if vin:
                        deal['vin'] = vin
                        dealership_deals.append(deal)
                
                return dealership_deals
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get dealership deals: {str(e)}")
            return []
    
    def _extract_vin_from_deal(self, deal: Dict[str, Any]) -> Optional[str]:
        """Extract VIN from deal custom fields or title"""
        
        # Check custom fields first
        custom_fields = deal.get('custom_fields', [])
        for field in custom_fields:
            if 'vin' in field.get('key', '').lower():
                return field.get('value', '')
        
        # Check title for VIN pattern
        title = deal.get('title', '')
        import re
        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', title.upper())
        if vin_match:
            return vin_match.group()
        
        return None
    
    def _create_vehicle_deal(self, vehicle: Dict[str, Any], dealership_name: str) -> Optional[int]:
        """Create new vehicle deal in PipeDrive"""
        
        try:
            # Build deal data
            deal_data = {
                'title': self._generate_deal_title(vehicle),
                'value': vehicle.get('price', 0),
                'currency': 'USD',
                'stage_id': self._get_default_stage_id(),
                'pipeline_id': self.config.pipeline_id,
                'status': 'open'
            }
            
            # Add custom fields
            custom_fields = self._build_vehicle_custom_fields(vehicle, dealership_name)
            deal_data.update(custom_fields)
            
            # Create deal
            response = self._make_api_request('POST', '/deals', data=deal_data)
            
            if response and response.get('success'):
                deal_id = response.get('data', {}).get('id')
                self.logger.info(f"✅ Created deal {deal_id} for {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}")
                
                # Add note with vehicle details
                self._add_vehicle_note(deal_id, vehicle)
                
                return deal_id
            else:
                self.logger.error(f"❌ Failed to create deal for VIN {vehicle.get('vin')}")
                return None
        
        except Exception as e:
            self.logger.error(f"❌ Error creating vehicle deal: {str(e)}")
            return None
    
    def _update_vehicle_deal(self, vehicle: Dict[str, Any], existing_deal: Dict[str, Any]) -> bool:
        """Update existing vehicle deal"""
        
        try:
            deal_id = existing_deal.get('id')
            
            # Build update data
            update_data = {
                'value': vehicle.get('price', 0),
                'title': self._generate_deal_title(vehicle)
            }
            
            # Update custom fields that may have changed
            custom_fields = self._build_vehicle_custom_fields(vehicle, existing_deal.get('dealership', ''))
            update_data.update(custom_fields)
            
            # Update deal
            response = self._make_api_request('PUT', f'/deals/{deal_id}', data=update_data)
            
            if response and response.get('success'):
                self.logger.info(f"✅ Updated deal {deal_id} for VIN {vehicle.get('vin')}")
                return True
            else:
                self.logger.error(f"❌ Failed to update deal {deal_id}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Error updating vehicle deal: {str(e)}")
            return False
    
    def _archive_vehicle_deal(self, deal: Dict[str, Any]) -> bool:
        """Archive deal for vehicle no longer in inventory"""
        
        try:
            deal_id = deal.get('id')
            
            # Update deal to mark as sold/archived
            update_data = {
                'status': 'lost',
                'lost_reason': 'Vehicle sold or removed from inventory'
            }
            
            response = self._make_api_request('PUT', f'/deals/{deal_id}', data=update_data)
            
            if response and response.get('success'):
                self.logger.info(f"📦 Archived deal {deal_id} for VIN {deal.get('vin')}")
                return True
            else:
                self.logger.error(f"❌ Failed to archive deal {deal_id}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Error archiving vehicle deal: {str(e)}")
            return False
    
    def _sync_vehicle_product(self, vehicle: Dict[str, Any], dealership_name: str) -> bool:
        """Sync vehicle as product for inventory tracking"""
        
        try:
            # Build product data
            product_data = {
                'name': f"{vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}",
                'code': vehicle.get('vin', ''),
                'unit': 'piece',
                'tax': 0,
                'active_flag': True,
                'selectable': True,
                'first_char': vehicle.get('make', '')[:1].upper() if vehicle.get('make') else 'U'
            }
            
            # Check if product already exists
            existing_product = self._find_product_by_vin(vehicle.get('vin', ''))
            
            if existing_product:
                # Update existing product
                product_id = existing_product.get('id')
                response = self._make_api_request('PUT', f'/products/{product_id}', data=product_data)
            else:
                # Create new product
                response = self._make_api_request('POST', '/products', data=product_data)
            
            if response and response.get('success'):
                return True
            else:
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Error syncing vehicle product: {str(e)}")
            return False
    
    def _find_product_by_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """Find existing product by VIN"""
        
        try:
            params = {
                'term': vin,
                'fields': 'code,name',
                'limit': 10
            }
            
            response = self._make_api_request('GET', '/products/search', params=params)
            
            if response and response.get('success'):
                products = response.get('data', {}).get('items', [])
                
                for product in products:
                    if product.get('code') == vin:
                        return product
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error finding product by VIN: {str(e)}")
            return None
    
    def _generate_deal_title(self, vehicle: Dict[str, Any]) -> str:
        """Generate deal title for vehicle"""
        
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        vin = vehicle.get('vin', '')
        
        title = f"{year} {make} {model}"
        if vin:
            title += f" - VIN: {vin[-8:]}"  # Last 8 characters of VIN
        
        return title.strip()
    
    def _build_vehicle_custom_fields(self, vehicle: Dict[str, Any], dealership_name: str) -> Dict[str, Any]:
        """Build custom fields for vehicle deal"""
        
        custom_fields = {}
        
        # Map common vehicle fields to PipeDrive custom fields
        field_mapping = {
            'vin': 'vin',
            'stock_number': 'stock_number',
            'mileage': 'mileage',
            'exterior_color': 'exterior_color',
            'interior_color': 'interior_color',
            'transmission': 'transmission',
            'engine': 'engine',
            'fuel_type': 'fuel_type',
            'condition': 'condition',
            'dealership': 'dealership_name'
        }
        
        for vehicle_field, pipedrive_field in field_mapping.items():
            if vehicle_field in vehicle and pipedrive_field in self.custom_fields_cache:
                field_id = self.custom_fields_cache[pipedrive_field]
                custom_fields[f"custom_fields.{field_id}"] = vehicle[vehicle_field]
        
        # Add dealership name
        if 'dealership_name' in self.custom_fields_cache:
            field_id = self.custom_fields_cache['dealership_name']
            custom_fields[f"custom_fields.{field_id}"] = dealership_name
        
        return custom_fields
    
    def _get_default_stage_id(self) -> Optional[int]:
        """Get default stage ID for new deals"""
        
        if self.config.pipeline_id and self.config.pipeline_id in self.stage_cache:
            stages = self.stage_cache[self.config.pipeline_id]
            
            # Look for common stage names
            for stage_name in ['new', 'lead', 'initial', 'qualified']:
                if stage_name in stages:
                    return stages[stage_name]
            
            # Return first stage as default
            if stages:
                return list(stages.values())[0]
        
        return None
    
    def _add_vehicle_note(self, deal_id: int, vehicle: Dict[str, Any]):
        """Add detailed vehicle note to deal"""
        
        try:
            # Build comprehensive vehicle note
            note_content = self._build_vehicle_note_content(vehicle)
            
            note_data = {
                'content': note_content,
                'deal_id': deal_id,
                'pinned_to_deal_flag': True
            }
            
            response = self._make_api_request('POST', '/notes', data=note_data)
            
            if response and response.get('success'):
                self.logger.info(f"📝 Added vehicle note to deal {deal_id}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to add vehicle note: {str(e)}")
    
    def _build_vehicle_note_content(self, vehicle: Dict[str, Any]) -> str:
        """Build detailed vehicle note content"""
        
        content = "🚗 **Vehicle Details**\n\n"
        
        # Basic info
        content += f"**VIN:** {vehicle.get('vin', 'N/A')}\n"
        content += f"**Stock #:** {vehicle.get('stock_number', 'N/A')}\n"
        content += f"**Year:** {vehicle.get('year', 'N/A')}\n"
        content += f"**Make:** {vehicle.get('make', 'N/A')}\n"
        content += f"**Model:** {vehicle.get('model', 'N/A')}\n"
        content += f"**Trim:** {vehicle.get('trim', 'N/A')}\n"
        content += f"**Condition:** {vehicle.get('condition', 'N/A')}\n"
        
        # Pricing
        if vehicle.get('price'):
            content += f"**Price:** ${vehicle['price']:,}\n"
        if vehicle.get('msrp'):
            content += f"**MSRP:** ${vehicle['msrp']:,}\n"
        
        # Details
        content += f"**Mileage:** {vehicle.get('mileage', 'N/A'):,} miles\n" if vehicle.get('mileage') else "**Mileage:** N/A\n"
        content += f"**Exterior Color:** {vehicle.get('exterior_color', 'N/A')}\n"
        content += f"**Interior Color:** {vehicle.get('interior_color', 'N/A')}\n"
        content += f"**Transmission:** {vehicle.get('transmission', 'N/A')}\n"
        content += f"**Engine:** {vehicle.get('engine', 'N/A')}\n"
        content += f"**Fuel Type:** {vehicle.get('fuel_type', 'N/A')}\n"
        
        # Dealership info
        content += f"\n**Dealership:** {vehicle.get('dealer_name', 'N/A')}\n"
        
        # Vehicle URL
        if vehicle.get('vehicle_url'):
            content += f"**Vehicle Page:** {vehicle['vehicle_url']}\n"
        
        # Scraped timestamp
        content += f"\n**Last Updated:** {vehicle.get('scraped_at', datetime.now().isoformat())}\n"
        
        return content
    
    def sync_inventory_alerts(self, alerts: List[InventoryAlert]) -> Dict[str, Any]:
        """
        Sync inventory alerts to PipeDrive as activities and notes
        """
        
        self.logger.info(f"📢 Syncing {len(alerts)} inventory alerts to PipeDrive...")
        
        sync_report = {
            'total_alerts': len(alerts),
            'activities_created': 0,
            'notes_created': 0,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            for alert in alerts:
                try:
                    # Create activity for high priority alerts
                    if alert.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]:
                        activity_success = self._create_alert_activity(alert)
                        if activity_success:
                            sync_report['activities_created'] += 1
                    
                    # Always create note for alert details
                    note_success = self._create_alert_note(alert)
                    if note_success:
                        sync_report['notes_created'] += 1
                
                except Exception as e:
                    error_msg = f"Alert sync error for {alert.alert_id}: {str(e)}"
                    sync_report['errors'].append(error_msg)
                    self.logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Alert sync failed: {str(e)}"
            sync_report['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return sync_report
    
    def _create_alert_activity(self, alert: InventoryAlert) -> bool:
        """Create PipeDrive activity for high-priority alert"""
        
        try:
            # Map alert types to activity types
            activity_type_mapping = {
                AlertType.PRICE_DROP: 'call',
                AlertType.NEW_VEHICLE: 'task',
                AlertType.INVENTORY_LOW: 'deadline',
                AlertType.VERIFICATION_FAILURE: 'task'
            }
            
            activity_data = {
                'subject': alert.title,
                'note': alert.message,
                'type': activity_type_mapping.get(alert.alert_type, 'task'),
                'due_date': datetime.now().date().isoformat(),
                'due_time': (datetime.now() + timedelta(hours=1)).time().strftime('%H:%M'),
                'duration': '01:00',  # 1 hour duration
                'done': 0  # Not completed
            }
            
            response = self._make_api_request('POST', '/activities', data=activity_data)
            
            if response and response.get('success'):
                activity_id = response.get('data', {}).get('id')
                self.logger.info(f"✅ Created activity {activity_id} for alert {alert.alert_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create alert activity: {str(e)}")
            return False
    
    def _create_alert_note(self, alert: InventoryAlert) -> bool:
        """Create PipeDrive note for alert"""
        
        try:
            # Build alert note content
            note_content = f"🚨 **{alert.title}**\n\n"
            note_content += f"**Priority:** {alert.priority.value.upper()}\n"
            note_content += f"**Type:** {alert.alert_type.value.replace('_', ' ').title()}\n"
            note_content += f"**Dealership:** {alert.dealership_name}\n"
            note_content += f"**Message:** {alert.message}\n"
            
            # Add details if available
            if alert.details:
                note_content += f"\n**Details:**\n```\n{json.dumps(alert.details, indent=2)}\n```\n"
            
            note_content += f"\n**Alert ID:** {alert.alert_id}\n"
            note_content += f"**Created:** {alert.created_at.isoformat()}\n"
            
            note_data = {
                'content': note_content
            }
            
            response = self._make_api_request('POST', '/notes', data=note_data)
            
            if response and response.get('success'):
                note_id = response.get('data', {}).get('id')
                self.logger.info(f"📝 Created note {note_id} for alert {alert.alert_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create alert note: {str(e)}")
            return False
    
    def sync_competitive_insights(self, insights: List[CompetitorInsight]) -> Dict[str, Any]:
        """
        Sync competitive pricing insights to PipeDrive
        """
        
        self.logger.info(f"🏆 Syncing {len(insights)} competitive insights to PipeDrive...")
        
        sync_report = {
            'total_insights': len(insights),
            'notes_created': 0,
            'deals_updated': 0,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            for insight in insights:
                try:
                    # Find related deal by VIN
                    deal = self._find_deal_by_vin(insight.vin)
                    
                    if deal:
                        # Add competitive insight note to deal
                        note_success = self._create_competitive_insight_note(insight, deal.get('id'))
                        if note_success:
                            sync_report['notes_created'] += 1
                        
                        # Update deal with competitive data
                        update_success = self._update_deal_with_competitive_data(deal.get('id'), insight)
                        if update_success:
                            sync_report['deals_updated'] += 1
                    else:
                        self.logger.warning(f"⚠️ No deal found for VIN {insight.vin}")
                
                except Exception as e:
                    error_msg = f"Competitive insight sync error for VIN {insight.vin}: {str(e)}"
                    sync_report['errors'].append(error_msg)
                    self.logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Competitive insights sync failed: {str(e)}"
            sync_report['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return sync_report
    
    def _find_deal_by_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """Find deal by VIN"""
        
        try:
            params = {
                'term': vin,
                'fields': 'title,custom_fields',
                'limit': 10
            }
            
            response = self._make_api_request('GET', '/deals/search', params=params)
            
            if response and response.get('success'):
                deals = response.get('data', {}).get('items', [])
                
                for deal in deals:
                    deal_vin = self._extract_vin_from_deal(deal)
                    if deal_vin == vin:
                        return deal
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error finding deal by VIN: {str(e)}")
            return None
    
    def _create_competitive_insight_note(self, insight: CompetitorInsight, deal_id: int) -> bool:
        """Create competitive insight note for deal"""
        
        try:
            # Build competitive insight note
            note_content = f"🏆 **Competitive Pricing Analysis**\n\n"
            note_content += f"**Competitor:** {insight.competitor_dealership}\n"
            note_content += f"**Our Price:** ${insight.our_price:,}\n"
            note_content += f"**Competitor Price:** ${insight.competitor_price:,}\n"
            
            if insight.price_advantage > 0:
                note_content += f"**Price Advantage:** ${insight.price_advantage:,} (We're cheaper! 🎯)\n"
            elif insight.price_advantage < 0:
                note_content += f"**Price Disadvantage:** ${abs(insight.price_advantage):,} (They're cheaper ⚠️)\n"
            else:
                note_content += f"**Price Match:** Prices are equal 🤝\n"
            
            note_content += f"**Market Position:** {insight.market_position}\n"
            note_content += f"**Priority:** {insight.priority}\n"
            note_content += f"\n**Insight:** {insight.insight_text}\n"
            note_content += f"\n**Analysis Date:** {insight.created_at.isoformat()}\n"
            
            note_data = {
                'content': note_content,
                'deal_id': deal_id,
                'pinned_to_deal_flag': True
            }
            
            response = self._make_api_request('POST', '/notes', data=note_data)
            
            if response and response.get('success'):
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create competitive insight note: {str(e)}")
            return False
    
    def _update_deal_with_competitive_data(self, deal_id: int, insight: CompetitorInsight) -> bool:
        """Update deal with competitive pricing data"""
        
        try:
            # Update custom fields with competitive data
            update_data = {}
            
            if 'competitor_price' in self.custom_fields_cache:
                field_id = self.custom_fields_cache['competitor_price']
                update_data[f"custom_fields.{field_id}"] = insight.competitor_price
            
            if 'price_advantage' in self.custom_fields_cache:
                field_id = self.custom_fields_cache['price_advantage']
                update_data[f"custom_fields.{field_id}"] = insight.price_advantage
            
            if 'market_position' in self.custom_fields_cache:
                field_id = self.custom_fields_cache['market_position']
                update_data[f"custom_fields.{field_id}"] = insight.market_position
            
            if update_data:
                response = self._make_api_request('PUT', f'/deals/{deal_id}', data=update_data)
                
                if response and response.get('success'):
                    return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"❌ Failed to update deal with competitive data: {str(e)}")
            return False
    
    def _log_sync_summary(self, sync_report: Dict[str, Any]):
        """Log comprehensive sync summary"""
        
        self.logger.info("=" * 80)
        self.logger.info(f"📊 PIPEDRIVE SYNC SUMMARY - {sync_report.get('dealership', 'Unknown')}")
        self.logger.info("=" * 80)
        self.logger.info(f"Total vehicles: {sync_report.get('total_vehicles', 0)}")
        self.logger.info(f"Deals created: {sync_report.get('deals_created', 0)}")
        self.logger.info(f"Deals updated: {sync_report.get('deals_updated', 0)}")
        self.logger.info(f"Deals archived: {sync_report.get('deals_archived', 0)}")
        self.logger.info(f"Products created: {sync_report.get('products_created', 0)}")
        self.logger.info(f"Products updated: {sync_report.get('products_updated', 0)}")
        self.logger.info(f"Sync duration: {sync_report.get('sync_duration', 0):.1f} seconds")
        
        errors = sync_report.get('errors', [])
        if errors:
            self.logger.info(f"Errors: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                self.logger.info(f"  ⚠️ {error}")
        else:
            self.logger.info("✅ No errors")
        
        self.logger.info("=" * 80)
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sync statistics"""
        
        if not self.sync_history:
            return {'message': 'No sync history available'}
        
        # Calculate aggregate statistics
        total_syncs = len(self.sync_history)
        total_vehicles = sum(sync.get('total_vehicles', 0) for sync in self.sync_history)
        total_deals_created = sum(sync.get('deals_created', 0) for sync in self.sync_history)
        total_deals_updated = sum(sync.get('deals_updated', 0) for sync in self.sync_history)
        total_errors = sum(len(sync.get('errors', [])) for sync in self.sync_history)
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_syncs = [
            sync for sync in self.sync_history 
            if datetime.fromisoformat(sync.get('timestamp', '')) > recent_cutoff
        ]
        
        return {
            'total_syncs': total_syncs,
            'total_vehicles_synced': total_vehicles,
            'total_deals_created': total_deals_created,
            'total_deals_updated': total_deals_updated,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_vehicles * 100) if total_vehicles > 0 else 0,
            'recent_syncs_24h': len(recent_syncs),
            'last_sync': self.sync_history[-1] if self.sync_history else None,
            'dealerships_synced': list(set(sync.get('dealership') for sync in self.sync_history))
        }

# Factory function for creating PipeDrive integration
def create_pipedrive_integration(
    api_token: str,
    company_domain: str,
    pipeline_id: Optional[int] = None,
    custom_field_mapping: Optional[Dict[str, int]] = None
) -> PipeDriveCRMIntegration:
    """Factory function to create PipeDrive CRM integration"""
    
    config = PipeDriveConfiguration(
        api_token=api_token,
        company_domain=company_domain,
        pipeline_id=pipeline_id,
        custom_field_mapping=custom_field_mapping or {}
    )
    
    return PipeDriveCRMIntegration(config)

# Integration helper for existing scrapers
def enhance_scraper_with_pipedrive(
    scraper_instance,
    pipedrive_integration: PipeDriveCRMIntegration
) -> None:
    """Enhance existing scraper with PipeDrive integration"""
    
    scraper_instance.pipedrive_integration = pipedrive_integration
    
    # Add PipeDrive sync method to scraper
    def sync_to_pipedrive(self, vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.pipedrive_integration.sync_vehicle_inventory(vehicles, self.dealership_name)
    
    # Bind method to scraper instance
    import types
    scraper_instance.sync_to_pipedrive = types.MethodType(sync_to_pipedrive, scraper_instance)