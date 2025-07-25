#!/usr/bin/env python3
"""
Silver Fox Monitoring & Alerting Configuration System
=====================================================

Centralized configuration and management system for monitoring and alerting
across the Silver Fox scraper ecosystem. Provides unified interface for
setting up, managing, and coordinating all monitoring and alerting systems.

Features:
- Unified monitoring configuration
- Alert rule management
- Notification channel configuration
- Dashboard setup and management
- Health check coordination
- Performance threshold management

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add silverfox_system to path for accessing existing modules
sys.path.insert(0, str(Path(__file__).parent / "silverfox_system" / "core" / "scrapers" / "utils"))

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"

class MetricType(Enum):
    """Types of metrics to monitor"""
    SCRAPER_PERFORMANCE = "scraper_performance"
    INVENTORY_CHANGES = "inventory_changes"
    SYSTEM_RESOURCES = "system_resources"
    API_RESPONSES = "api_responses"
    DATA_QUALITY = "data_quality"
    BUSINESS_METRICS = "business_metrics"

@dataclass
class AlertRule:
    """Configuration for an alert rule"""
    name: str
    description: str
    metric_type: MetricType
    condition: str  # e.g., "cpu_usage > 80", "response_time > 30"
    severity: AlertSeverity
    notification_channels: List[NotificationChannel]
    enabled: bool = True
    cooldown_minutes: int = 15
    evaluation_interval_seconds: int = 60
    threshold_value: float = 0
    metadata: Dict[str, Any] = None

@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]
    test_endpoint: Optional[str] = None

@dataclass
class DashboardConfig:
    """Configuration for monitoring dashboards"""
    name: str
    description: str
    panels: List[Dict[str, Any]]
    refresh_interval: str = "30s"
    time_range: str = "1h"
    tags: List[str] = None

class MonitoringAlertingConfig:
    """
    Centralized monitoring and alerting configuration system
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize monitoring configuration system"""
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "monitoring_config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize components
        self.alert_rules = self._load_alert_rules()
        self.notification_configs = self._load_notification_configs()
        self.dashboard_configs = self._load_dashboard_configs()
        
        # State tracking
        self.active_alerts = {}
        self.alert_history = []
        
        self.logger.info("✅ Monitoring & alerting configuration system initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load main configuration"""
        default_config = {
            'monitoring': {
                'enabled': True,
                'data_retention_days': 30,
                'metrics_interval_seconds': 30,
                'health_check_interval_seconds': 60,
                'alert_evaluation_interval_seconds': 60
            },
            'alerting': {
                'enabled': True,
                'default_cooldown_minutes': 15,
                'max_alerts_per_hour': 50,
                'escalation_enabled': True,
                'escalation_delay_minutes': 30
            },
            'notifications': {
                'rate_limit_per_minute': 10,
                'retry_attempts': 3,
                'retry_delay_seconds': 30
            },
            'dashboards': {
                'auto_generate': True,
                'refresh_interval': '30s',
                'default_time_range': '1h'
            },
            'system_thresholds': {
                'cpu_warning': 70,
                'cpu_critical': 85,
                'memory_warning': 80,
                'memory_critical': 90,
                'disk_warning': 75,
                'disk_critical': 85,
                'response_time_warning': 10,
                'response_time_critical': 30,
                'error_rate_warning': 5,
                'error_rate_critical': 10
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('monitoring_alerting_config')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"monitoring_alerting_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_alert_rules(self) -> Dict[str, AlertRule]:
        """Load alert rules configuration"""
        rules = {}
        
        # Define default alert rules
        default_rules = [
            AlertRule(
                name="scraper_high_response_time",
                description="Scraper response time exceeds threshold",
                metric_type=MetricType.SCRAPER_PERFORMANCE,
                condition="response_time > 30",
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                threshold_value=30,
                metadata={"unit": "seconds", "aggregation": "avg"}
            ),
            AlertRule(
                name="scraper_failure_rate_high",
                description="Scraper failure rate is too high",
                metric_type=MetricType.SCRAPER_PERFORMANCE,
                condition="error_rate > 10",
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                threshold_value=10,
                metadata={"unit": "percent", "aggregation": "avg"}
            ),
            AlertRule(
                name="inventory_significant_change",
                description="Significant change in inventory detected",
                metric_type=MetricType.INVENTORY_CHANGES,
                condition="inventory_change_percent > 20",
                severity=AlertSeverity.INFO,
                notification_channels=[NotificationChannel.EMAIL],
                threshold_value=20,
                metadata={"unit": "percent", "aggregation": "change"}
            ),
            AlertRule(
                name="system_high_cpu_usage",
                description="System CPU usage is high",
                metric_type=MetricType.SYSTEM_RESOURCES,
                condition="cpu_usage > 85",
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                threshold_value=85,
                metadata={"unit": "percent", "aggregation": "avg"}
            ),
            AlertRule(
                name="system_high_memory_usage",
                description="System memory usage is high",
                metric_type=MetricType.SYSTEM_RESOURCES,
                condition="memory_usage > 90",
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                threshold_value=90,
                metadata={"unit": "percent", "aggregation": "avg"}
            ),
            AlertRule(
                name="data_quality_low",
                description="Data quality score is below acceptable threshold",
                metric_type=MetricType.DATA_QUALITY,
                condition="data_quality_score < 0.8",
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                threshold_value=0.8,
                metadata={"unit": "score", "aggregation": "avg"}
            ),
            AlertRule(
                name="api_error_rate_high",
                description="API error rate is too high",
                metric_type=MetricType.API_RESPONSES,
                condition="api_error_rate > 5",
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                threshold_value=5,
                metadata={"unit": "percent", "aggregation": "rate"}
            ),
            AlertRule(
                name="vehicles_scraped_low",
                description="Number of vehicles scraped is below expected",
                metric_type=MetricType.BUSINESS_METRICS,
                condition="vehicles_scraped < 500",
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                threshold_value=500,
                metadata={"unit": "count", "aggregation": "sum"}
            )
        ]
        
        # Add default rules
        for rule in default_rules:
            rules[rule.name] = rule
        
        # Load custom rules from file
        rules_file = self.config_dir / "alert_rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    custom_rules_data = json.load(f)
                
                for rule_data in custom_rules_data:
                    rule = AlertRule(**rule_data)
                    rules[rule.name] = rule
                    
            except Exception as e:
                self.logger.warning(f"Could not load custom alert rules: {e}")
        
        self.logger.info(f"📋 Loaded {len(rules)} alert rules")
        return rules
    
    def _load_notification_configs(self) -> Dict[str, NotificationConfig]:
        """Load notification channel configurations"""
        configs = {}
        
        # Email configuration
        configs['email'] = NotificationConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            config={
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('SMTP_USERNAME', ''),
                'password': os.getenv('SMTP_PASSWORD', ''),
                'from_email': os.getenv('FROM_EMAIL', 'alerts@silverfoxmarketing.com'),
                'recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
                'use_tls': True
            },
            test_endpoint='smtp_test'
        )
        
        # Slack configuration
        configs['slack'] = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=bool(os.getenv('SLACK_WEBHOOK_URL')),
            config={
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
                'channel': os.getenv('SLACK_CHANNEL', '#silverfox-alerts'),
                'username': os.getenv('SLACK_USERNAME', 'SilverFox Bot'),
                'icon_emoji': ':robot_face:'
            },
            test_endpoint='slack_test'
        )
        
        # Webhook configuration
        configs['webhook'] = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=bool(os.getenv('WEBHOOK_URL')),
            config={
                'url': os.getenv('WEBHOOK_URL', ''),
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'timeout': 10
            },
            test_endpoint='webhook_test'
        )
        
        # Discord configuration
        configs['discord'] = NotificationConfig(
            channel=NotificationChannel.DISCORD,
            enabled=bool(os.getenv('DISCORD_WEBHOOK_URL')),
            config={
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),
                'username': 'SilverFox Monitor',
                'avatar_url': None
            },
            test_endpoint='discord_test'
        )
        
        return configs
    
    def _load_dashboard_configs(self) -> Dict[str, DashboardConfig]:
        """Load dashboard configurations"""
        dashboards = {}
        
        # Main system overview dashboard
        dashboards['system_overview'] = DashboardConfig(
            name="Silver Fox System Overview",
            description="High-level overview of the Silver Fox scraper system",
            panels=[
                {
                    'title': 'Active Scrapers',
                    'type': 'stat',
                    'targets': [{'expr': 'count(up{job="silverfox-scrapers"})'}],
                    'unit': 'short'
                },
                {
                    'title': 'Total Vehicles Scraped (24h)',
                    'type': 'stat',
                    'targets': [{'expr': 'sum(increase(vehicles_scraped_total[24h]))'}],
                    'unit': 'short'
                },
                {
                    'title': 'System CPU Usage',
                    'type': 'graph',
                    'targets': [{'expr': 'avg(cpu_usage_percent)'}],
                    'unit': 'percent'
                },
                {
                    'title': 'System Memory Usage',
                    'type': 'graph',
                    'targets': [{'expr': 'avg(memory_usage_percent)'}],
                    'unit': 'percent'
                },
                {
                    'title': 'Scraper Response Times',
                    'type': 'graph',
                    'targets': [{'expr': 'avg(scraper_response_time_seconds) by (scraper)'}],
                    'unit': 's'
                },
                {
                    'title': 'Error Rate',
                    'type': 'graph',
                    'targets': [{'expr': 'rate(scraper_errors_total[5m])'}],
                    'unit': 'percent'
                }
            ],
            tags=['overview', 'system']
        )
        
        # Scraper performance dashboard
        dashboards['scraper_performance'] = DashboardConfig(
            name="Scraper Performance",
            description="Detailed performance metrics for individual scrapers",
            panels=[
                {
                    'title': 'Scraper Success Rate',
                    'type': 'table',
                    'targets': [{'expr': 'avg(scraper_success_rate) by (scraper)'}],
                    'unit': 'percent'
                },
                {
                    'title': 'Vehicles per Scraper',
                    'type': 'bar',
                    'targets': [{'expr': 'sum(vehicles_scraped_total) by (scraper)'}],
                    'unit': 'short'
                },
                {
                    'title': 'Response Time Distribution',
                    'type': 'heatmap',
                    'targets': [{'expr': 'histogram_quantile(0.95, scraper_response_time_seconds)'}],
                    'unit': 's'
                }
            ],
            tags=['performance', 'scrapers']
        )
        
        # Business metrics dashboard
        dashboards['business_metrics'] = DashboardConfig(
            name="Business Metrics",
            description="Business-focused metrics and KPIs",
            panels=[
                {
                    'title': 'Total Inventory Value',
                    'type': 'stat',
                    'targets': [{'expr': 'sum(inventory_total_value)'}],
                    'unit': 'currencyUSD'
                },
                {
                    'title': 'Average Vehicle Price',
                    'type': 'stat',
                    'targets': [{'expr': 'avg(vehicle_average_price)'}],
                    'unit': 'currencyUSD'
                },
                {
                    'title': 'Inventory Changes Over Time',
                    'type': 'graph',
                    'targets': [{'expr': 'sum(inventory_change) by (dealer)'}],
                    'unit': 'short'
                },
                {
                    'title': 'Top Dealers by Inventory',
                    'type': 'pie',
                    'targets': [{'expr': 'sum(inventory_count) by (dealer)'}],
                    'unit': 'short'
                }
            ],
            tags=['business', 'kpi']
        )
        
        return dashboards
    
    def create_alert_rule(self, rule: AlertRule) -> bool:
        """Create a new alert rule"""
        try:
            self.alert_rules[rule.name] = rule
            self._save_alert_rules()
            self.logger.info(f"✅ Created alert rule: {rule.name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to create alert rule {rule.name}: {e}")
            return False
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule"""
        try:
            if rule_name not in self.alert_rules:
                self.logger.warning(f"⚠️ Alert rule {rule_name} not found")
                return False
            
            rule = self.alert_rules[rule_name]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self._save_alert_rules()
            self.logger.info(f"✅ Updated alert rule: {rule_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to update alert rule {rule_name}: {e}")
            return False
    
    def delete_alert_rule(self, rule_name: str) -> bool:
        """Delete an alert rule"""
        try:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                self._save_alert_rules()
                self.logger.info(f"✅ Deleted alert rule: {rule_name}")
                return True
            else:
                self.logger.warning(f"⚠️ Alert rule {rule_name} not found")
                return False
        except Exception as e:
            self.logger.error(f"❌ Failed to delete alert rule {rule_name}: {e}")
            return False
    
    def _save_alert_rules(self):
        """Save alert rules to file"""
        try:
            rules_file = self.config_dir / "alert_rules.json"
            rules_data = [asdict(rule) for rule in self.alert_rules.values()]
            
            with open(rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save alert rules: {e}")
    
    def send_test_notification(self, channel: NotificationChannel) -> bool:
        """Send test notification to verify channel configuration"""
        try:
            if channel.value not in self.notification_configs:
                self.logger.error(f"❌ Notification channel {channel.value} not configured")
                return False
            
            config = self.notification_configs[channel.value]
            if not config.enabled:
                self.logger.warning(f"⚠️ Notification channel {channel.value} is disabled")
                return False
            
            test_message = {
                'title': 'Silver Fox Test Alert',
                'message': 'This is a test notification from the Silver Fox scraper system.',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            }
            
            success = self._send_notification(channel, test_message)
            
            if success:
                self.logger.info(f"✅ Test notification sent successfully to {channel.value}")
            else:
                self.logger.error(f"❌ Test notification failed for {channel.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Test notification failed: {e}")
            return False
    
    def _send_notification(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """Send notification to specified channel"""
        try:
            config = self.notification_configs[channel.value]
            
            if channel == NotificationChannel.EMAIL:
                return self._send_email_notification(config.config, message)
            elif channel == NotificationChannel.SLACK:
                return self._send_slack_notification(config.config, message)
            elif channel == NotificationChannel.WEBHOOK:
                return self._send_webhook_notification(config.config, message)
            elif channel == NotificationChannel.DISCORD:
                return self._send_discord_notification(config.config, message)
            else:
                self.logger.warning(f"⚠️ Unsupported notification channel: {channel.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send notification: {e}")
            return False
    
    def _send_email_notification(self, config: Dict[str, Any], message: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['recipients'])
            msg['Subject'] = f"[SilverFox Alert] {message['title']}"
            
            body = f"""
Silver Fox Scraper System Alert

Title: {message['title']}
Severity: {message['severity'].upper()}
Time: {message['timestamp']}

Message:
{message['message']}

---
This alert was generated by the Silver Fox Scraper System monitoring.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls'):
                server.starttls()
            
            if config['username'] and config['password']:
                server.login(config['username'], config['password'])
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Email notification failed: {e}")
            return False
    
    def _send_slack_notification(self, config: Dict[str, Any], message: Dict[str, Any]) -> bool:
        """Send Slack notification"""
        try:
            webhook_url = config['webhook_url']
            if not webhook_url:
                return False
            
            # Choose color based on severity
            color_map = {
                'info': '#36a64f',      # Green
                'warning': '#ff9500',   # Orange
                'critical': '#ff0000',  # Red
                'emergency': '#800080'  # Purple
            }
            
            slack_message = {
                'channel': config.get('channel', '#silverfox-alerts'),
                'username': config.get('username', 'SilverFox Bot'),
                'icon_emoji': config.get('icon_emoji', ':robot_face:'),
                'attachments': [{
                    'color': color_map.get(message['severity'], '#cccccc'),
                    'title': message['title'],
                    'text': message['message'],
                    'fields': [
                        {
                            'title': 'Severity',
                            'value': message['severity'].upper(),
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': message['timestamp'],
                            'short': True
                        }
                    ],
                    'footer': 'Silver Fox Scraper System',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(webhook_url, json=slack_message, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ Slack notification failed: {e}")
            return False
    
    def _send_webhook_notification(self, config: Dict[str, Any], message: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            webhook_url = config['url']
            if not webhook_url:
                return False
            
            payload = {
                'source': 'silverfox_scraper_system',
                'alert': message,
                'timestamp': datetime.now().isoformat()
            }
            
            headers = config.get('headers', {'Content-Type': 'application/json'})
            timeout = config.get('timeout', 10)
            method = config.get('method', 'POST').upper()
            
            if method == 'POST':
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(webhook_url, json=payload, headers=headers, timeout=timeout)
            else:
                self.logger.error(f"❌ Unsupported webhook method: {method}")
                return False
            
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            self.logger.error(f"❌ Webhook notification failed: {e}")
            return False
    
    def _send_discord_notification(self, config: Dict[str, Any], message: Dict[str, Any]) -> bool:
        """Send Discord notification"""
        try:
            webhook_url = config['webhook_url']
            if not webhook_url:
                return False
            
            # Choose embed color based on severity
            color_map = {
                'info': 0x36a64f,      # Green
                'warning': 0xff9500,   # Orange
                'critical': 0xff0000,  # Red
                'emergency': 0x800080  # Purple
            }
            
            discord_message = {
                'username': config.get('username', 'SilverFox Monitor'),
                'avatar_url': config.get('avatar_url'),
                'embeds': [{
                    'title': message['title'],
                    'description': message['message'],
                    'color': color_map.get(message['severity'], 0xcccccc),
                    'fields': [
                        {
                            'name': 'Severity',
                            'value': message['severity'].upper(),
                            'inline': True
                        },
                        {
                            'name': 'Time',
                            'value': message['timestamp'],
                            'inline': True
                        }
                    ],
                    'footer': {
                        'text': 'Silver Fox Scraper System'
                    },
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            response = requests.post(webhook_url, json=discord_message, timeout=10)
            return response.status_code == 204  # Discord returns 204 for success
            
        except Exception as e:
            self.logger.error(f"❌ Discord notification failed: {e}")
            return False
    
    def generate_prometheus_config(self) -> str:
        """Generate Prometheus configuration for metrics collection"""
        prometheus_config = {
            'global': {
                'scrape_interval': '30s',
                'evaluation_interval': '30s'
            },
            'rule_files': [
                'silverfox_alert_rules.yml'
            ],
            'scrape_configs': [
                {
                    'job_name': 'silverfox-scrapers',
                    'static_configs': [{
                        'targets': ['localhost:9090']
                    }],
                    'scrape_interval': '30s',
                    'metrics_path': '/metrics'
                },
                {
                    'job_name': 'silverfox-system',
                    'static_configs': [{
                        'targets': ['localhost:9091']
                    }],
                    'scrape_interval': '15s',
                    'metrics_path': '/system-metrics'
                }
            ],
            'alerting': {
                'alertmanagers': [{
                    'static_configs': [{
                        'targets': ['localhost:9093']
                    }]
                }]
            }
        }
        
        return yaml.dump(prometheus_config, default_flow_style=False)
    
    def generate_grafana_dashboard(self, dashboard_name: str) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        if dashboard_name not in self.dashboard_configs:
            return {}
        
        dashboard = self.dashboard_configs[dashboard_name]
        
        grafana_dashboard = {
            'dashboard': {
                'id': None,
                'title': dashboard.name,
                'description': dashboard.description,
                'tags': dashboard.tags or [],
                'timezone': 'browser',
                'refresh': dashboard.refresh_interval,
                'time': {
                    'from': f'now-{dashboard.time_range}',
                    'to': 'now'
                },
                'panels': dashboard.panels,
                'version': 1
            }
        }
        
        return grafana_dashboard
    
    def export_configuration(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export complete monitoring configuration"""
        config_export = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'alert_rules': [asdict(rule) for rule in self.alert_rules.values()],
            'notification_configs': {
                name: asdict(config) for name, config in self.notification_configs.items()
            },
            'dashboard_configs': {
                name: asdict(config) for name, config in self.dashboard_configs.items()
            },
            'system_config': self.config
        }
        
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    json.dump(config_export, f, indent=2, default=str)
                self.logger.info(f"📄 Configuration exported to: {output_path}")
            except Exception as e:
                self.logger.error(f"❌ Failed to export configuration: {e}")
        
        return config_export
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system monitoring status"""
        return {
            'monitoring_enabled': self.config['monitoring']['enabled'],
            'alerting_enabled': self.config['alerting']['enabled'],
            'total_alert_rules': len(self.alert_rules),
            'active_alert_rules': len([r for r in self.alert_rules.values() if r.enabled]),
            'notification_channels': {
                name: config.enabled for name, config in self.notification_configs.items()
            },
            'active_alerts': len(self.active_alerts),
            'dashboard_count': len(self.dashboard_configs),
            'last_updated': datetime.now().isoformat()
        }


def main():
    """Main execution for command-line usage"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Silver Fox Monitoring & Alerting Config')
    parser.add_argument('--export', type=str, help='Export configuration to file')
    parser.add_argument('--test-email', action='store_true', help='Test email notifications')
    parser.add_argument('--test-slack', action='store_true', help='Test Slack notifications')
    parser.add_argument('--generate-prometheus', action='store_true', help='Generate Prometheus config')
    parser.add_argument('--generate-grafana', type=str, help='Generate Grafana dashboard')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    args = parser.parse_args()
    
    print("⚙️ Silver Fox Monitoring & Alerting Configuration")
    print("=" * 50)
    
    # Initialize configuration system
    config_system = MonitoringAlertingConfig(args.config)
    
    if args.status:
        print("📊 System Status:")
        status = config_system.get_system_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.test_email:
        print("📧 Testing email notifications...")
        success = config_system.send_test_notification(NotificationChannel.EMAIL)
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    elif args.test_slack:
        print("💬 Testing Slack notifications...")
        success = config_system.send_test_notification(NotificationChannel.SLACK)
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    elif args.generate_prometheus:
        print("📊 Generating Prometheus configuration...")
        prometheus_config = config_system.generate_prometheus_config()
        print(prometheus_config)
    
    elif args.generate_grafana:
        print(f"📈 Generating Grafana dashboard: {args.generate_grafana}")
        dashboard = config_system.generate_grafana_dashboard(args.generate_grafana)
        if dashboard:
            print(json.dumps(dashboard, indent=2))
        else:
            print(f"❌ Dashboard '{args.generate_grafana}' not found")
    
    elif args.export:
        print(f"💾 Exporting configuration to: {args.export}")
        config_system.export_configuration(args.export)
        print("✅ Export completed")
    
    else:
        print("📋 Available options:")
        print("  --status              : Show system status")
        print("  --test-email          : Test email notifications")
        print("  --test-slack          : Test Slack notifications")
        print("  --generate-prometheus : Generate Prometheus config")
        print("  --generate-grafana <name> : Generate Grafana dashboard")
        print("  --export <file>       : Export configuration")


if __name__ == "__main__":
    main()