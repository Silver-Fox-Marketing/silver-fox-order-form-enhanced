#!/usr/bin/env python3
"""
Real-Time Inventory Alerts System
Monitors inventory changes and sends notifications for significant events
Integrates with scrapers to provide actionable business intelligence
"""

import logging
import json
import time
import smtplib
import requests
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

# Import verification system for inventory validation
try:
    from enhanced_inventory_verification import (
        EnhancedInventoryVerificationSystem,
        InventoryStatus,
        VehicleValidation
    )
except ImportError:
    from utils.enhanced_inventory_verification import (
        EnhancedInventoryVerificationSystem,
        InventoryStatus,
        VehicleValidation
    )

class AlertType(Enum):
    """Types of inventory alerts"""
    NEW_VEHICLE = "new_vehicle"
    SOLD_VEHICLE = "sold_vehicle"
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    INVENTORY_LOW = "inventory_low"
    INVENTORY_HIGH = "inventory_high"
    RAPID_TURNOVER = "rapid_turnover"
    STALE_INVENTORY = "stale_inventory"
    COMPETITOR_ALERT = "competitor_alert"
    VERIFICATION_FAILURE = "verification_failure"
    SCRAPER_FAILURE = "scraper_failure"

class AlertPriority(Enum):
    """Priority levels for alerts"""
    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"         # Important, notify within 1 hour
    MEDIUM = "medium"     # Notable, notify within 4 hours
    LOW = "low"          # Informational, batch notifications

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PIPEDRIVE = "pipedrive"
    SLACK = "slack"
    DASHBOARD = "dashboard"

@dataclass
class InventoryAlert:
    """Individual inventory alert"""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    dealership_name: str
    dealership_id: str
    title: str
    message: str
    details: Dict[str, Any]
    created_at: datetime
    channels: List[NotificationChannel] = field(default_factory=list)
    sent: bool = False
    sent_at: Optional[datetime] = None
    
@dataclass
class VehicleChange:
    """Represents a change in vehicle status or attributes"""
    vin: str
    change_type: str  # new, sold, price_change, status_change
    old_value: Any
    new_value: Any
    timestamp: datetime
    confidence: float = 1.0

@dataclass
class InventorySnapshot:
    """Point-in-time inventory snapshot"""
    dealership_id: str
    timestamp: datetime
    total_count: int
    new_count: int
    used_count: int
    certified_count: int
    vehicles: Dict[str, Dict[str, Any]]  # VIN -> vehicle data
    hash: str = ""
    
    def __post_init__(self):
        """Calculate snapshot hash after initialization"""
        if not self.hash:
            self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate hash of inventory snapshot for change detection"""
        vehicle_data = json.dumps(self.vehicles, sort_keys=True)
        return hashlib.sha256(vehicle_data.encode()).hexdigest()

class RealtimeInventoryAlertSystem:
    """
    Real-time inventory monitoring and alert system
    Tracks changes, identifies patterns, and sends actionable notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("RealtimeInventoryAlerts")
        
        # Alert configuration
        self.alert_thresholds = {
            'price_drop_percentage': config.get('price_drop_threshold', 5.0),
            'price_increase_percentage': config.get('price_increase_threshold', 10.0),
            'low_inventory_count': config.get('low_inventory_threshold', 10),
            'high_inventory_count': config.get('high_inventory_threshold', 200),
            'stale_days': config.get('stale_inventory_days', 90),
            'rapid_turnover_days': config.get('rapid_turnover_days', 7)
        }
        
        # Notification configuration
        self.notification_config = {
            'email': config.get('email_config', {}),
            'sms': config.get('sms_config', {}),
            'webhook': config.get('webhook_config', {}),
            'slack': config.get('slack_config', {}),
            'pipedrive': config.get('pipedrive_config', {})
        }
        
        # State tracking
        self.inventory_snapshots = {}  # dealership_id -> [snapshots]
        self.active_alerts = []
        self.sent_alerts = []
        self.vehicle_history = {}  # VIN -> [changes]
        
        # Initialize notification handlers
        self._initialize_notification_handlers()
    
    def _initialize_notification_handlers(self):
        """Initialize notification channel handlers"""
        self.notification_handlers = {}
        
        if self.notification_config['email']:
            self.notification_handlers[NotificationChannel.EMAIL] = self._send_email_notification
        
        if self.notification_config['webhook']:
            self.notification_handlers[NotificationChannel.WEBHOOK] = self._send_webhook_notification
        
        if self.notification_config['slack']:
            self.notification_handlers[NotificationChannel.SLACK] = self._send_slack_notification
        
        if self.notification_config['pipedrive']:
            self.notification_handlers[NotificationChannel.PIPEDRIVE] = self._send_pipedrive_notification
    
    def process_inventory_update(self, 
                               dealership_id: str,
                               dealership_name: str,
                               current_vehicles: List[Dict[str, Any]],
                               verification_report: Optional[Dict[str, Any]] = None) -> List[InventoryAlert]:
        """
        Process inventory update and generate alerts
        Returns list of generated alerts
        """
        
        self.logger.info(f"Processing inventory update for {dealership_name}")
        
        # Create current snapshot
        current_snapshot = self._create_inventory_snapshot(dealership_id, current_vehicles)
        
        # Get previous snapshot for comparison
        previous_snapshot = self._get_previous_snapshot(dealership_id)
        
        # Initialize alert list
        alerts = []
        
        # Check verification report first
        if verification_report:
            verification_alerts = self._check_verification_alerts(
                dealership_id, dealership_name, verification_report
            )
            alerts.extend(verification_alerts)
        
        if previous_snapshot:
            # Detect changes between snapshots
            changes = self._detect_inventory_changes(previous_snapshot, current_snapshot)
            
            # Generate alerts based on changes
            change_alerts = self._generate_change_alerts(
                dealership_id, dealership_name, changes, current_snapshot
            )
            alerts.extend(change_alerts)
            
            # Check for pattern-based alerts
            pattern_alerts = self._check_pattern_alerts(
                dealership_id, dealership_name, current_snapshot, previous_snapshot
            )
            alerts.extend(pattern_alerts)
        else:
            # First snapshot for this dealership
            self.logger.info(f"First inventory snapshot for {dealership_name}")
        
        # Store current snapshot
        self._store_snapshot(dealership_id, current_snapshot)
        
        # Process and send alerts
        if alerts:
            self._process_alerts(alerts)
        
        return alerts
    
    def _create_inventory_snapshot(self, 
                                 dealership_id: str,
                                 vehicles: List[Dict[str, Any]]) -> InventorySnapshot:
        """Create inventory snapshot from vehicle list"""
        
        vehicles_dict = {}
        new_count = 0
        used_count = 0
        certified_count = 0
        
        for vehicle in vehicles:
            vin = vehicle.get('vin', '')
            if vin:
                vehicles_dict[vin] = vehicle
                
                condition = vehicle.get('condition', '').lower()
                if 'new' in condition:
                    new_count += 1
                elif 'certified' in condition:
                    certified_count += 1
                else:
                    used_count += 1
        
        snapshot = InventorySnapshot(
            dealership_id=dealership_id,
            timestamp=datetime.now(),
            total_count=len(vehicles_dict),
            new_count=new_count,
            used_count=used_count,
            certified_count=certified_count,
            vehicles=vehicles_dict
        )
        
        return snapshot
    
    def _get_previous_snapshot(self, dealership_id: str) -> Optional[InventorySnapshot]:
        """Get most recent previous snapshot for dealership"""
        
        if dealership_id in self.inventory_snapshots:
            snapshots = self.inventory_snapshots[dealership_id]
            if snapshots:
                return snapshots[-1]
        
        return None
    
    def _store_snapshot(self, dealership_id: str, snapshot: InventorySnapshot):
        """Store inventory snapshot"""
        
        if dealership_id not in self.inventory_snapshots:
            self.inventory_snapshots[dealership_id] = []
        
        self.inventory_snapshots[dealership_id].append(snapshot)
        
        # Keep only last 30 days of snapshots
        cutoff_date = datetime.now() - timedelta(days=30)
        self.inventory_snapshots[dealership_id] = [
            s for s in self.inventory_snapshots[dealership_id]
            if s.timestamp > cutoff_date
        ]
    
    def _detect_inventory_changes(self,
                                previous: InventorySnapshot,
                                current: InventorySnapshot) -> List[VehicleChange]:
        """Detect changes between inventory snapshots"""
        
        changes = []
        
        previous_vins = set(previous.vehicles.keys())
        current_vins = set(current.vehicles.keys())
        
        # New vehicles
        new_vins = current_vins - previous_vins
        for vin in new_vins:
            changes.append(VehicleChange(
                vin=vin,
                change_type='new',
                old_value=None,
                new_value=current.vehicles[vin],
                timestamp=current.timestamp
            ))
        
        # Sold/removed vehicles
        sold_vins = previous_vins - current_vins
        for vin in sold_vins:
            changes.append(VehicleChange(
                vin=vin,
                change_type='sold',
                old_value=previous.vehicles[vin],
                new_value=None,
                timestamp=current.timestamp
            ))
        
        # Changed vehicles
        common_vins = previous_vins & current_vins
        for vin in common_vins:
            old_vehicle = previous.vehicles[vin]
            new_vehicle = current.vehicles[vin]
            
            # Check price changes
            old_price = old_vehicle.get('price')
            new_price = new_vehicle.get('price')
            
            if old_price and new_price and old_price != new_price:
                changes.append(VehicleChange(
                    vin=vin,
                    change_type='price_change',
                    old_value=old_price,
                    new_value=new_price,
                    timestamp=current.timestamp
                ))
            
            # Check status changes
            old_status = old_vehicle.get('normalized_status', '')
            new_status = new_vehicle.get('normalized_status', '')
            
            if old_status != new_status:
                changes.append(VehicleChange(
                    vin=vin,
                    change_type='status_change',
                    old_value=old_status,
                    new_value=new_status,
                    timestamp=current.timestamp
                ))
        
        return changes
    
    def _generate_change_alerts(self,
                              dealership_id: str,
                              dealership_name: str,
                              changes: List[VehicleChange],
                              current_snapshot: InventorySnapshot) -> List[InventoryAlert]:
        """Generate alerts based on detected changes"""
        
        alerts = []
        
        # Group changes by type
        new_vehicles = [c for c in changes if c.change_type == 'new']
        sold_vehicles = [c for c in changes if c.change_type == 'sold']
        price_changes = [c for c in changes if c.change_type == 'price_change']
        
        # New vehicle alerts
        if new_vehicles:
            for change in new_vehicles[:5]:  # Limit to top 5 to avoid spam
                vehicle = change.new_value
                alert = InventoryAlert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.NEW_VEHICLE,
                    priority=AlertPriority.MEDIUM,
                    dealership_name=dealership_name,
                    dealership_id=dealership_id,
                    title=f"New Vehicle Added: {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}",
                    message=f"New {vehicle.get('condition', 'vehicle')} added to inventory at ${vehicle.get('price', 'N/A'):,}",
                    details={
                        'vin': change.vin,
                        'vehicle': vehicle,
                        'added_at': change.timestamp.isoformat()
                    },
                    created_at=datetime.now(),
                    channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
                )
                alerts.append(alert)
        
        # Sold vehicle alerts
        if sold_vehicles:
            # Batch notification for multiple sales
            if len(sold_vehicles) > 3:
                alert = InventoryAlert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.SOLD_VEHICLE,
                    priority=AlertPriority.HIGH,
                    dealership_name=dealership_name,
                    dealership_id=dealership_id,
                    title=f"{len(sold_vehicles)} Vehicles Sold",
                    message=f"{len(sold_vehicles)} vehicles were sold since last update",
                    details={
                        'sold_count': len(sold_vehicles),
                        'sold_vehicles': [c.old_value for c in sold_vehicles[:10]]
                    },
                    created_at=datetime.now(),
                    channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
                )
                alerts.append(alert)
        
        # Price drop alerts
        significant_price_drops = []
        for change in price_changes:
            if change.old_value and change.new_value:
                price_drop_pct = ((change.old_value - change.new_value) / change.old_value) * 100
                
                if price_drop_pct >= self.alert_thresholds['price_drop_percentage']:
                    significant_price_drops.append({
                        'vin': change.vin,
                        'vehicle': current_snapshot.vehicles.get(change.vin, {}),
                        'old_price': change.old_value,
                        'new_price': change.new_value,
                        'drop_percentage': price_drop_pct
                    })
        
        if significant_price_drops:
            for drop in significant_price_drops[:3]:  # Top 3 price drops
                vehicle = drop['vehicle']
                alert = InventoryAlert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.PRICE_DROP,
                    priority=AlertPriority.HIGH,
                    dealership_name=dealership_name,
                    dealership_id=dealership_id,
                    title=f"Price Drop: {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}",
                    message=f"Price reduced by {drop['drop_percentage']:.1f}% from ${drop['old_price']:,} to ${drop['new_price']:,}",
                    details=drop,
                    created_at=datetime.now(),
                    channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK]
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_pattern_alerts(self,
                            dealership_id: str,
                            dealership_name: str,
                            current: InventorySnapshot,
                            previous: InventorySnapshot) -> List[InventoryAlert]:
        """Check for pattern-based alerts (inventory levels, turnover, etc.)"""
        
        alerts = []
        
        # Check inventory levels
        if current.total_count <= self.alert_thresholds['low_inventory_count']:
            alert = InventoryAlert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.INVENTORY_LOW,
                priority=AlertPriority.HIGH,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title=f"Low Inventory Alert: {current.total_count} vehicles",
                message=f"Inventory has dropped to {current.total_count} vehicles, below threshold of {self.alert_thresholds['low_inventory_count']}",
                details={
                    'current_count': current.total_count,
                    'threshold': self.alert_thresholds['low_inventory_count'],
                    'breakdown': {
                        'new': current.new_count,
                        'used': current.used_count,
                        'certified': current.certified_count
                    }
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS]
            )
            alerts.append(alert)
        
        # Check for stale inventory
        stale_vehicles = []
        for vin, vehicle in current.vehicles.items():
            # Check if vehicle has been in inventory too long
            if self._is_stale_inventory(vehicle):
                stale_vehicles.append(vehicle)
        
        if len(stale_vehicles) > 5:  # More than 5 stale vehicles
            alert = InventoryAlert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.STALE_INVENTORY,
                priority=AlertPriority.MEDIUM,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title=f"Stale Inventory Alert: {len(stale_vehicles)} vehicles",
                message=f"{len(stale_vehicles)} vehicles have been in inventory over {self.alert_thresholds['stale_days']} days",
                details={
                    'stale_count': len(stale_vehicles),
                    'threshold_days': self.alert_thresholds['stale_days'],
                    'sample_vehicles': stale_vehicles[:5]
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
            )
            alerts.append(alert)
        
        # Check for rapid turnover
        if self._has_rapid_turnover(dealership_id, current, previous):
            alert = InventoryAlert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.RAPID_TURNOVER,
                priority=AlertPriority.MEDIUM,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title="High Inventory Turnover Detected",
                message=f"Significant inventory changes detected in past {self.alert_thresholds['rapid_turnover_days']} days",
                details={
                    'current_total': current.total_count,
                    'previous_total': previous.total_count,
                    'change_percentage': abs(current.total_count - previous.total_count) / previous.total_count * 100
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL]
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_verification_alerts(self,
                                 dealership_id: str,
                                 dealership_name: str,
                                 verification_report: Dict[str, Any]) -> List[InventoryAlert]:
        """Generate alerts based on verification report"""
        
        alerts = []
        
        confidence_score = verification_report.get('confidence_score', 0.0)
        discrepancies = verification_report.get('discrepancies', [])
        
        # Low confidence alert
        if confidence_score < 0.6:
            alert = InventoryAlert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.VERIFICATION_FAILURE,
                priority=AlertPriority.HIGH,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title=f"Low Inventory Verification Confidence: {confidence_score:.1%}",
                message="Inventory verification confidence is below acceptable threshold",
                details={
                    'confidence_score': confidence_score,
                    'discrepancies': discrepancies,
                    'recommendations': verification_report.get('recommendations', [])
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
            )
            alerts.append(alert)
        
        # High severity discrepancies
        high_severity_discrepancies = [d for d in discrepancies if d.get('severity') == 'high']
        if high_severity_discrepancies:
            alert = InventoryAlert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.VERIFICATION_FAILURE,
                priority=AlertPriority.CRITICAL,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title=f"Critical Inventory Discrepancies Detected",
                message=f"{len(high_severity_discrepancies)} high-severity discrepancies found in inventory verification",
                details={
                    'discrepancy_count': len(high_severity_discrepancies),
                    'discrepancies': high_severity_discrepancies
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK]
            )
            alerts.append(alert)
        
        return alerts
    
    def _is_stale_inventory(self, vehicle: Dict[str, Any]) -> bool:
        """Check if vehicle is stale inventory"""
        
        # Check multiple date fields
        date_fields = ['date_in_stock', 'listed_date', 'created_at']
        
        for field in date_fields:
            if field in vehicle and vehicle[field]:
                try:
                    # Parse date
                    if isinstance(vehicle[field], str):
                        stock_date = datetime.fromisoformat(vehicle[field].replace('Z', '+00:00'))
                    else:
                        stock_date = vehicle[field]
                    
                    # Calculate days in stock
                    days_in_stock = (datetime.now() - stock_date).days
                    
                    if days_in_stock > self.alert_thresholds['stale_days']:
                        return True
                        
                except Exception:
                    continue
        
        # Check days_in_stock field directly
        if 'days_in_stock' in vehicle:
            try:
                days = int(vehicle['days_in_stock'])
                if days > self.alert_thresholds['stale_days']:
                    return True
            except:
                pass
        
        return False
    
    def _has_rapid_turnover(self,
                          dealership_id: str,
                          current: InventorySnapshot,
                          previous: InventorySnapshot) -> bool:
        """Check if dealership has rapid inventory turnover"""
        
        if not previous:
            return False
        
        # Calculate time between snapshots
        time_diff = current.timestamp - previous.timestamp
        
        # Only check if snapshots are recent enough
        if time_diff.days > self.alert_thresholds['rapid_turnover_days']:
            return False
        
        # Calculate inventory change percentage
        if previous.total_count > 0:
            change_pct = abs(current.total_count - previous.total_count) / previous.total_count * 100
            
            # Consider 20% change as rapid
            if change_pct > 20:
                return True
        
        # Check vehicle turnover
        previous_vins = set(previous.vehicles.keys())
        current_vins = set(current.vehicles.keys())
        
        # Calculate percentage of inventory that changed
        total_vins = len(previous_vins | current_vins)
        changed_vins = len(previous_vins ^ current_vins)  # Symmetric difference
        
        if total_vins > 0:
            turnover_pct = (changed_vins / total_vins) * 100
            
            # Consider 30% turnover as rapid
            if turnover_pct > 30:
                return True
        
        return False
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = int(time.time() * 1000000)
        random_component = hash(str(timestamp)) % 10000
        return f"alert_{timestamp}_{random_component}"
    
    def _process_alerts(self, alerts: List[InventoryAlert]):
        """Process and send alerts based on priority and channels"""
        
        # Sort by priority
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3
        }
        
        alerts.sort(key=lambda a: priority_order[a.priority])
        
        # Process each alert
        for alert in alerts:
            try:
                # Send to configured channels
                for channel in alert.channels:
                    if channel in self.notification_handlers:
                        handler = self.notification_handlers[channel]
                        handler(alert)
                
                # Mark as sent
                alert.sent = True
                alert.sent_at = datetime.now()
                
                # Store alert
                self.active_alerts.append(alert)
                
                self.logger.info(f"Alert sent: {alert.title} via {[c.value for c in alert.channels]}")
                
            except Exception as e:
                self.logger.error(f"Failed to process alert {alert.alert_id}: {str(e)}")
    
    def _send_email_notification(self, alert: InventoryAlert):
        """Send email notification"""
        
        email_config = self.notification_config['email']
        
        if not email_config:
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(email_config['to_addresses'])
            msg['Subject'] = f"[{alert.priority.value.upper()}] {alert.title}"
            
            # Create HTML body
            html_body = self._create_email_body(alert)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                
                if email_config.get('username') and email_config.get('password'):
                    server.login(email_config['username'], email_config['password'])
                
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
    
    def _send_webhook_notification(self, alert: InventoryAlert):
        """Send webhook notification"""
        
        webhook_config = self.notification_config['webhook']
        
        if not webhook_config:
            return
        
        try:
            payload = {
                'alert_id': alert.alert_id,
                'alert_type': alert.alert_type.value,
                'priority': alert.priority.value,
                'dealership': {
                    'name': alert.dealership_name,
                    'id': alert.dealership_id
                },
                'title': alert.title,
                'message': alert.message,
                'details': alert.details,
                'created_at': alert.created_at.isoformat()
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=30
            )
            
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")
    
    def _send_slack_notification(self, alert: InventoryAlert):
        """Send Slack notification"""
        
        slack_config = self.notification_config['slack']
        
        if not slack_config:
            return
        
        try:
            # Create Slack message
            color_map = {
                AlertPriority.CRITICAL: '#FF0000',
                AlertPriority.HIGH: '#FF9900',
                AlertPriority.MEDIUM: '#FFCC00',
                AlertPriority.LOW: '#00CC00'
            }
            
            attachment = {
                'color': color_map[alert.priority],
                'title': alert.title,
                'text': alert.message,
                'fields': [
                    {
                        'title': 'Dealership',
                        'value': alert.dealership_name,
                        'short': True
                    },
                    {
                        'title': 'Alert Type',
                        'value': alert.alert_type.value.replace('_', ' ').title(),
                        'short': True
                    }
                ],
                'footer': 'Silver Fox Inventory Alerts',
                'ts': int(alert.created_at.timestamp())
            }
            
            payload = {
                'channel': slack_config['channel'],
                'attachments': [attachment]
            }
            
            response = requests.post(
                slack_config['webhook_url'],
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _send_pipedrive_notification(self, alert: InventoryAlert):
        """Send notification to PipeDrive CRM"""
        
        # Placeholder for PipeDrive integration
        # Will be implemented when developing PipeDrive integration module
        pass
    
    def _create_email_body(self, alert: InventoryAlert) -> str:
        """Create HTML email body for alert"""
        
        priority_colors = {
            AlertPriority.CRITICAL: '#FF0000',
            AlertPriority.HIGH: '#FF9900',
            AlertPriority.MEDIUM: '#FFCC00',
            AlertPriority.LOW: '#00CC00'
        }
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: {priority_colors[alert.priority]}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .details {{ background-color: #f5f5f5; padding: 15px; margin-top: 20px; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{alert.title}</h2>
                <p>Priority: {alert.priority.value.upper()} | Type: {alert.alert_type.value.replace('_', ' ').title()}</p>
            </div>
            <div class="content">
                <p><strong>Dealership:</strong> {alert.dealership_name}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <div class="details">
                    <h3>Details</h3>
                    <pre>{json.dumps(alert.details, indent=2)}</pre>
                </div>
                
                <div class="footer">
                    <p>Generated by Silver Fox Inventory Alert System</p>
                    <p>Alert ID: {alert.alert_id} | Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_active_alerts(self, 
                         dealership_id: Optional[str] = None,
                         alert_type: Optional[AlertType] = None,
                         priority: Optional[AlertPriority] = None) -> List[InventoryAlert]:
        """Get active alerts with optional filtering"""
        
        alerts = self.active_alerts
        
        if dealership_id:
            alerts = [a for a in alerts if a.dealership_id == dealership_id]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert activity"""
        
        # Count alerts by type
        type_counts = {}
        for alert_type in AlertType:
            count = sum(1 for a in self.active_alerts if a.alert_type == alert_type)
            type_counts[alert_type.value] = count
        
        # Count alerts by priority
        priority_counts = {}
        for priority in AlertPriority:
            count = sum(1 for a in self.active_alerts if a.priority == priority)
            priority_counts[priority.value] = count
        
        # Get recent alerts
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_alerts = [a for a in self.active_alerts if a.created_at > recent_cutoff]
        
        return {
            'total_active_alerts': len(self.active_alerts),
            'alerts_by_type': type_counts,
            'alerts_by_priority': priority_counts,
            'recent_alerts_24h': len(recent_alerts),
            'sent_alerts': sum(1 for a in self.active_alerts if a.sent),
            'pending_alerts': sum(1 for a in self.active_alerts if not a.sent)
        }

# Factory function for creating alert system
def create_alert_system(config: Dict[str, Any]) -> RealtimeInventoryAlertSystem:
    """Create configured alert system instance"""
    
    # Default configuration
    default_config = {
        'price_drop_threshold': 5.0,
        'price_increase_threshold': 10.0,
        'low_inventory_threshold': 10,
        'high_inventory_threshold': 200,
        'stale_inventory_days': 90,
        'rapid_turnover_days': 7,
        'email_config': {},
        'webhook_config': {},
        'slack_config': {},
        'pipedrive_config': {}
    }
    
    # Merge with provided config
    merged_config = {**default_config, **config}
    
    return RealtimeInventoryAlertSystem(merged_config)