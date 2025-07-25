#!/usr/bin/env python3
"""
Silver Fox Real-Time Inventory Monitor
======================================

Real-time monitoring system for tracking scraper performance, inventory changes,
and dealer data quality across the entire Silver Fox scraper ecosystem.

Features:
- Real-time scraper performance monitoring
- Inventory change detection and alerting
- Data quality scoring and trends
- Automated issue detection and escalation
- Performance metrics dashboard data

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
import hashlib

# Import Silver Fox components
sys.path.append(str(Path(__file__).parent))
from network_utils import NetworkHandler
from production_fallback_handler import ProductionFallbackHandler

@dataclass
class InventorySnapshot:
    """Represents a point-in-time inventory snapshot"""
    dealer_id: str
    dealer_name: str
    timestamp: datetime
    vehicle_count: int
    total_value: float
    avg_price: float
    data_quality_score: float
    scraper_performance: Dict[str, Any]
    checksum: str

@dataclass
class PerformanceMetrics:
    """Scraper performance metrics"""
    dealer_id: str
    execution_time: float
    success_rate: float
    error_count: int
    last_successful_run: datetime
    consecutive_failures: int
    health_status: str  # 'healthy', 'warning', 'critical'

@dataclass
class AlertCondition:
    """Alert condition configuration"""
    name: str
    condition_type: str  # 'inventory_change', 'performance_issue', 'data_quality'
    threshold: float
    severity: str  # 'info', 'warning', 'critical'
    enabled: bool
    callback: Optional[Callable]

class RealTimeInventoryMonitor:
    """
    Real-time monitoring system for Silver Fox scraper ecosystem
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the monitoring system"""
        self.project_root = Path(__file__).parent
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize database
        self.db_path = self.project_root / "monitoring_data.db"
        self._initialize_database()
        
        # Initialize components
        self.network_handler = NetworkHandler()
        self.fallback_handler = ProductionFallbackHandler()
        
        # Monitoring state
        self.monitoring_active = False
        self.dealer_configs = self._load_dealer_configs()
        self.performance_cache = {}
        self.alert_conditions = self._initialize_alert_conditions()
        
        # Threading
        self.monitor_thread = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.logger.info("✅ Real-time inventory monitor initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            'monitoring_interval': 300,  # 5 minutes
            'data_retention_days': 30,
            'alert_thresholds': {
                'inventory_change_percent': 15.0,
                'performance_degradation': 50.0,
                'data_quality_minimum': 0.8,
                'consecutive_failure_limit': 3
            },
            'dealers': {
                'enabled': 'all',  # or list of dealer IDs
                'priority_dealers': [
                    'bmwofweststlouis',
                    'columbiabmw',
                    'jaguarranchomirage'
                ]
            },
            'notifications': {
                'email_enabled': False,
                'slack_enabled': False,
                'webhook_url': None
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('inventory_monitor')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"inventory_monitor_{datetime.now().strftime('%Y%m%d')}.log"
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
    
    def _initialize_database(self):
        """Initialize SQLite database for monitoring data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Inventory snapshots table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inventory_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dealer_id TEXT NOT NULL,
                        dealer_name TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        vehicle_count INTEGER NOT NULL,
                        total_value REAL NOT NULL,
                        avg_price REAL NOT NULL,
                        data_quality_score REAL NOT NULL,
                        scraper_performance TEXT NOT NULL,
                        checksum TEXT NOT NULL,
                        UNIQUE(dealer_id, timestamp)
                    )
                ''')
                
                # Performance metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dealer_id TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        execution_time REAL NOT NULL,
                        success_rate REAL NOT NULL,
                        error_count INTEGER NOT NULL,
                        last_successful_run DATETIME,
                        consecutive_failures INTEGER NOT NULL,
                        health_status TEXT NOT NULL
                    )
                ''')
                
                # Alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        dealer_id TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_inventory_dealer_time 
                    ON inventory_snapshots(dealer_id, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_performance_dealer_time 
                    ON performance_metrics(dealer_id, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_alerts_time 
                    ON alerts(timestamp)
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _load_dealer_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load dealer configurations from config files"""
        configs = {}
        config_dir = self.project_root / "silverfox_system" / "config"
        
        if not config_dir.exists():
            self.logger.warning(f"Config directory not found: {config_dir}")
            return configs
        
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    dealer_config = json.load(f)
                    dealer_id = config_file.stem
                    configs[dealer_id] = dealer_config
            except Exception as e:
                self.logger.warning(f"Could not load config for {config_file.stem}: {e}")
        
        self.logger.info(f"📋 Loaded configurations for {len(configs)} dealers")
        return configs
    
    def _initialize_alert_conditions(self) -> List[AlertCondition]:
        """Initialize alert conditions based on configuration"""
        conditions = []
        
        # Inventory change alerts
        conditions.append(AlertCondition(
            name="inventory_significant_change",
            condition_type="inventory_change",
            threshold=self.config['alert_thresholds']['inventory_change_percent'],
            severity="warning",
            enabled=True,
            callback=self._handle_inventory_change_alert
        ))
        
        # Performance degradation alerts
        conditions.append(AlertCondition(
            name="performance_degradation",
            condition_type="performance_issue",
            threshold=self.config['alert_thresholds']['performance_degradation'],
            severity="warning",
            enabled=True,
            callback=self._handle_performance_alert
        ))
        
        # Data quality alerts
        conditions.append(AlertCondition(
            name="data_quality_low",
            condition_type="data_quality",
            threshold=self.config['alert_thresholds']['data_quality_minimum'],
            severity="critical",
            enabled=True,
            callback=self._handle_data_quality_alert
        ))
        
        # Consecutive failure alerts
        conditions.append(AlertCondition(
            name="consecutive_failures",
            condition_type="performance_issue",
            threshold=self.config['alert_thresholds']['consecutive_failure_limit'],
            severity="critical",
            enabled=True,
            callback=self._handle_failure_alert
        ))
        
        return conditions
    
    def start_monitoring(self):
        """Start the real-time monitoring system"""
        if self.monitoring_active:
            self.logger.warning("⚠️ Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("🚀 Real-time inventory monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.executor.shutdown(wait=True)
        self.logger.info("🛑 Real-time inventory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("📊 Starting monitoring loop")
        
        while self.monitoring_active:
            try:
                # Get list of dealers to monitor
                dealers_to_monitor = self._get_dealers_to_monitor()
                
                # Monitor all dealers concurrently
                monitoring_tasks = []
                for dealer_id in dealers_to_monitor:
                    future = self.executor.submit(self._monitor_dealer, dealer_id)
                    monitoring_tasks.append((dealer_id, future))
                
                # Collect results
                for dealer_id, future in monitoring_tasks:
                    try:
                        snapshot = future.result(timeout=60)  # 1 minute timeout per dealer
                        if snapshot:
                            self._process_snapshot(snapshot)
                    except Exception as e:
                        self.logger.error(f"❌ Monitoring failed for {dealer_id}: {e}")
                        self._record_monitoring_failure(dealer_id, str(e))
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Sleep until next monitoring cycle
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(30)  # Short sleep before retry
    
    def _get_dealers_to_monitor(self) -> List[str]:
        """Get list of dealers to monitor based on configuration"""
        if self.config['dealers']['enabled'] == 'all':
            return list(self.dealer_configs.keys())
        elif isinstance(self.config['dealers']['enabled'], list):
            return self.config['dealers']['enabled']
        else:
            return list(self.dealer_configs.keys())
    
    def _monitor_dealer(self, dealer_id: str) -> Optional[InventorySnapshot]:
        """Monitor a single dealer and return snapshot"""
        try:
            start_time = time.time()
            
            # Import and instantiate scraper
            scraper = self._get_scraper_instance(dealer_id)
            if not scraper:
                return None
            
            # Get vehicle data
            vehicles = scraper.get_all_vehicles()
            execution_time = time.time() - start_time
            
            # Calculate metrics
            vehicle_count = len(vehicles) if vehicles else 0
            total_value = sum(v.get('price', 0) for v in vehicles if v.get('price'))
            avg_price = total_value / vehicle_count if vehicle_count > 0 else 0
            
            # Calculate data quality score
            data_quality_score = self._calculate_data_quality_score(vehicles)
            
            # Create performance metrics
            performance_metrics = {
                'execution_time': execution_time,
                'vehicle_count': vehicle_count,
                'success': vehicle_count > 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Create checksum for change detection
            vehicle_data_str = json.dumps(sorted([
                f"{v.get('vin', '')}-{v.get('price', 0)}" for v in vehicles
            ]))
            checksum = hashlib.md5(vehicle_data_str.encode()).hexdigest()
            
            # Create snapshot
            snapshot = InventorySnapshot(
                dealer_id=dealer_id,
                dealer_name=self.dealer_configs.get(dealer_id, {}).get('name', dealer_id),
                timestamp=datetime.now(),
                vehicle_count=vehicle_count,
                total_value=total_value,
                avg_price=avg_price,
                data_quality_score=data_quality_score,
                scraper_performance=performance_metrics,
                checksum=checksum
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"❌ Failed to monitor {dealer_id}: {e}")
            return None
    
    def _get_scraper_instance(self, dealer_id: str):
        """Get scraper instance for dealer"""
        try:
            # Import scraper module
            scraper_module_path = (
                self.project_root / "silverfox_system" / "core" / 
                "scrapers" / "dealerships" / f"{dealer_id}_optimized.py"
            )
            
            if not scraper_module_path.exists():
                self.logger.warning(f"⚠️ Scraper not found: {scraper_module_path}")
                return None
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(dealer_id, scraper_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find scraper class
            scraper_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('OptimizedScraper') and 
                    hasattr(attr, 'get_all_vehicles')):
                    scraper_class = attr
                    break
            
            if scraper_class:
                return scraper_class()
            else:
                self.logger.warning(f"⚠️ No scraper class found in {dealer_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to import scraper {dealer_id}: {e}")
            return None
    
    def _calculate_data_quality_score(self, vehicles: List[Dict[str, Any]]) -> float:
        """Calculate data quality score for vehicle data"""
        if not vehicles:
            return 0.0
        
        total_score = 0.0
        required_fields = ['vin', 'year', 'make', 'model', 'price']
        
        for vehicle in vehicles:
            field_score = 0.0
            
            for field in required_fields:
                if vehicle.get(field):
                    if field == 'vin' and len(str(vehicle[field])) == 17:
                        field_score += 0.3  # VIN is critical
                    elif field == 'price' and float(vehicle[field]) > 0:
                        field_score += 0.25
                    elif field in ['year', 'make', 'model'] and vehicle[field]:
                        field_score += 0.15
            
            total_score += field_score
        
        return min(total_score / len(vehicles), 1.0)
    
    def _process_snapshot(self, snapshot: InventorySnapshot):
        """Process a new inventory snapshot"""
        try:
            # Store snapshot in database
            self._store_snapshot(snapshot)
            
            # Check for alerts
            self._check_alert_conditions(snapshot)
            
            # Update performance cache
            self._update_performance_cache(snapshot)
            
            self.logger.info(
                f"📊 {snapshot.dealer_name}: {snapshot.vehicle_count} vehicles, "
                f"quality: {snapshot.data_quality_score:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process snapshot for {snapshot.dealer_id}: {e}")
    
    def _store_snapshot(self, snapshot: InventorySnapshot):
        """Store inventory snapshot in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO inventory_snapshots
                    (dealer_id, dealer_name, timestamp, vehicle_count, total_value,
                     avg_price, data_quality_score, scraper_performance, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.dealer_id,
                    snapshot.dealer_name,
                    snapshot.timestamp,
                    snapshot.vehicle_count,
                    snapshot.total_value,
                    snapshot.avg_price,
                    snapshot.data_quality_score,
                    json.dumps(snapshot.scraper_performance),
                    snapshot.checksum
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store snapshot: {e}")
    
    def _check_alert_conditions(self, snapshot: InventorySnapshot):
        """Check if any alert conditions are met"""
        for condition in self.alert_conditions:
            if not condition.enabled:
                continue
            
            try:
                if self._evaluate_alert_condition(condition, snapshot):
                    self._trigger_alert(condition, snapshot)
            except Exception as e:
                self.logger.error(f"❌ Error evaluating alert condition {condition.name}: {e}")
    
    def _evaluate_alert_condition(self, condition: AlertCondition, snapshot: InventorySnapshot) -> bool:
        """Evaluate if an alert condition is met"""
        if condition.condition_type == "inventory_change":
            return self._check_inventory_change(condition, snapshot)
        elif condition.condition_type == "data_quality":
            return snapshot.data_quality_score < condition.threshold
        elif condition.condition_type == "performance_issue":
            return self._check_performance_issue(condition, snapshot)
        
        return False
    
    def _check_inventory_change(self, condition: AlertCondition, snapshot: InventorySnapshot) -> bool:
        """Check for significant inventory changes"""
        try:
            # Get previous snapshot
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT vehicle_count FROM inventory_snapshots
                    WHERE dealer_id = ? AND timestamp < ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (snapshot.dealer_id, snapshot.timestamp))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                previous_count = result[0]
                current_count = snapshot.vehicle_count
                
                if previous_count == 0:
                    return False
                
                change_percent = abs(current_count - previous_count) / previous_count * 100
                return change_percent > condition.threshold
                
        except Exception as e:
            self.logger.error(f"❌ Error checking inventory change: {e}")
            return False
    
    def _check_performance_issue(self, condition: AlertCondition, snapshot: InventorySnapshot) -> bool:
        """Check for performance issues"""
        execution_time = snapshot.scraper_performance.get('execution_time', 0)
        
        # Check if execution time is too high (condition.threshold is max acceptable time in seconds)
        if condition.name == "performance_degradation":
            return execution_time > condition.threshold
        elif condition.name == "consecutive_failures":
            # This would need to be checked against historical data
            return False  # Simplified for now
        
        return False
    
    def _trigger_alert(self, condition: AlertCondition, snapshot: InventorySnapshot):
        """Trigger an alert"""
        message = self._generate_alert_message(condition, snapshot)
        
        # Store alert in database
        self._store_alert(condition, snapshot, message)
        
        # Call condition callback if available
        if condition.callback:
            try:
                condition.callback(condition, snapshot, message)
            except Exception as e:
                self.logger.error(f"❌ Alert callback failed: {e}")
        
        # Log alert
        log_level = getattr(logging, condition.severity.upper(), logging.INFO)
        self.logger.log(log_level, f"🚨 ALERT: {message}")
    
    def _generate_alert_message(self, condition: AlertCondition, snapshot: InventorySnapshot) -> str:
        """Generate human-readable alert message"""
        if condition.condition_type == "inventory_change":
            return (f"Significant inventory change detected for {snapshot.dealer_name}: "
                   f"{snapshot.vehicle_count} vehicles")
        elif condition.condition_type == "data_quality":
            return (f"Low data quality for {snapshot.dealer_name}: "
                   f"{snapshot.data_quality_score:.2f} (threshold: {condition.threshold})")
        elif condition.condition_type == "performance_issue":
            execution_time = snapshot.scraper_performance.get('execution_time', 0)
            return (f"Performance issue for {snapshot.dealer_name}: "
                   f"{execution_time:.1f}s execution time")
        
        return f"Alert condition {condition.name} triggered for {snapshot.dealer_name}"
    
    def _store_alert(self, condition: AlertCondition, snapshot: InventorySnapshot, message: str):
        """Store alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts
                    (timestamp, dealer_id, alert_type, severity, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    snapshot.dealer_id,
                    condition.condition_type,
                    condition.severity,
                    message
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Failed to store alert: {e}")
    
    def _update_performance_cache(self, snapshot: InventorySnapshot):
        """Update performance metrics cache"""
        self.performance_cache[snapshot.dealer_id] = {
            'last_update': snapshot.timestamp,
            'vehicle_count': snapshot.vehicle_count,
            'execution_time': snapshot.scraper_performance.get('execution_time', 0),
            'data_quality': snapshot.data_quality_score,
            'checksum': snapshot.checksum
        }
    
    def _record_monitoring_failure(self, dealer_id: str, error_message: str):
        """Record a monitoring failure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts
                    (timestamp, dealer_id, alert_type, severity, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    dealer_id,
                    'monitoring_failure',
                    'critical',
                    f"Monitoring failed: {error_message}"
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Failed to record monitoring failure: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['data_retention_days'])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old snapshots
                cursor.execute('''
                    DELETE FROM inventory_snapshots WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean up old performance metrics
                cursor.execute('''
                    DELETE FROM performance_metrics WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean up resolved alerts older than 7 days
                alert_cutoff = datetime.now() - timedelta(days=7)
                cursor.execute('''
                    DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE
                ''', (alert_cutoff,))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Data cleanup failed: {e}")
    
    # Alert callback handlers
    def _handle_inventory_change_alert(self, condition: AlertCondition, snapshot: InventorySnapshot, message: str):
        """Handle inventory change alerts"""
        # Could integrate with notification systems here
        pass
    
    def _handle_performance_alert(self, condition: AlertCondition, snapshot: InventorySnapshot, message: str):
        """Handle performance alerts"""
        # Could trigger automatic retries or fallback mechanisms
        pass
    
    def _handle_data_quality_alert(self, condition: AlertCondition, snapshot: InventorySnapshot, message: str):
        """Handle data quality alerts"""
        # Could trigger scraper validation or reconfiguration
        pass
    
    def _handle_failure_alert(self, condition: AlertCondition, snapshot: InventorySnapshot, message: str):
        """Handle consecutive failure alerts"""
        # Could trigger emergency fallback or admin notification
        pass
    
    # Public API methods
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'monitoring_active': self.monitoring_active,
            'dealers_monitored': len(self.dealer_configs),
            'last_update': datetime.now().isoformat(),
            'performance_cache': dict(self.performance_cache)
        }
    
    def get_dealer_history(self, dealer_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical data for a specific dealer"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM inventory_snapshots
                    WHERE dealer_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (dealer_id, cutoff_time))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    row_dict['scraper_performance'] = json.loads(row_dict['scraper_performance'])
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get dealer history: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM alerts
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (cutoff_time,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get recent alerts: {e}")
            return []


def main():
    """Main execution for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Silver Fox Real-Time Inventory Monitor")
    print("=" * 50)
    
    # Initialize monitor
    monitor = RealTimeInventoryMonitor()
    
    try:
        # Start monitoring
        monitor.start_monitoring()
        
        print("✅ Monitoring started. Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(60)
            status = monitor.get_current_status()
            print(f"📊 Status: {status['dealers_monitored']} dealers monitored")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
        monitor.stop_monitoring()
        print("✅ Monitor stopped")


if __name__ == "__main__":
    main()