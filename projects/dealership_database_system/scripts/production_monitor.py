"""
Production monitoring system for Silver Fox Marketing dealership database
Provides real-time monitoring, alerting, and health checks for production operations
"""
import time
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Callable
import psutil
import os
from threading import Thread, Event
from database_connection import db_manager
from database_config import config
from data_validator import DataValidator
from performance_monitor import PerformanceMonitor
from error_recovery import DatabaseRecoveryManager
from consistency_checker import ConsistencyChecker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Comprehensive production monitoring system"""
    
    def __init__(self, config_file: str = None):
        self.db = db_manager
        self.validator = DataValidator()
        self.performance_monitor = PerformanceMonitor()
        self.recovery_manager = DatabaseRecoveryManager()
        self.consistency_checker = ConsistencyChecker()
        
        # Load monitoring configuration
        self.config = self.load_monitoring_config(config_file)
        
        # Monitoring state
        self.is_running = False
        self.stop_event = Event()
        self.monitoring_thread = None
        self.alert_history = []
        
        # Metrics storage
        self.metrics_history = []
        self.current_alerts = []
    
    def load_monitoring_config(self, config_file: str = None) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'monitoring_interval': 300,  # 5 minutes
            'health_check_interval': 900,  # 15 minutes
            'performance_check_interval': 1800,  # 30 minutes
            'consistency_check_interval': 3600,  # 1 hour
            
            'thresholds': {
                'cpu_usage_critical': 90,
                'cpu_usage_warning': 75,
                'memory_usage_critical': 90,
                'memory_usage_warning': 80,
                'disk_usage_critical': 90,
                'disk_usage_warning': 85,
                'database_size_warning_gb': 50,
                'database_size_critical_gb': 100,
                'slow_query_threshold': 10.0,
                'import_delay_warning_hours': 24,
                'import_delay_critical_hours': 48
            },
            
            'alerting': {
                'enabled': False,
                'email': {
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_address': 'silverfox-db@localhost',
                    'to_addresses': []
                },
                'alert_cooldown': 3600,  # 1 hour between duplicate alerts
                'critical_alert_cooldown': 300  # 5 minutes for critical alerts
            },
            
            'data_quality': {
                'max_missing_vins_per_import': 10,
                'max_invalid_prices_per_import': 5,
                'max_duplicate_vins_per_dealer': 3,
                'min_vehicles_per_active_dealer': 10
            },
            
            'backup': {
                'auto_backup_on_critical': True,
                'backup_retention_days': 30
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def check_system_health(self) -> Dict:
        """Comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'system_metrics': {},
            'database_metrics': {},
            'issues': [],
            'alerts_triggered': []
        }
        
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
            
            health_status['system_metrics'] = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': (disk.used / disk.total) * 100,
                'available_memory_gb': memory.available / (1024**3),
                'free_disk_gb': disk.free / (1024**3)
            }
            
            # Check system thresholds
            if cpu_percent >= self.config['thresholds']['cpu_usage_critical']:
                issue = {'type': 'critical', 'metric': 'cpu_usage', 'value': cpu_percent}
                health_status['issues'].append(issue)
                health_status['overall_status'] = 'critical'
            elif cpu_percent >= self.config['thresholds']['cpu_usage_warning']:
                issue = {'type': 'warning', 'metric': 'cpu_usage', 'value': cpu_percent}
                health_status['issues'].append(issue)
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            
            if memory.percent >= self.config['thresholds']['memory_usage_critical']:
                issue = {'type': 'critical', 'metric': 'memory_usage', 'value': memory.percent}
                health_status['issues'].append(issue)
                health_status['overall_status'] = 'critical'
            elif memory.percent >= self.config['thresholds']['memory_usage_warning']:
                issue = {'type': 'warning', 'metric': 'memory_usage', 'value': memory.percent}
                health_status['issues'].append(issue)
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            
            # Database connectivity and metrics
            try:
                if self.recovery_manager.test_database_connectivity():
                    # Get database size
                    db_size_result = self.db.execute_query("""
                        SELECT pg_database_size(current_database()) / (1024*1024*1024.0) as size_gb
                    """, fetch='one')
                    
                    db_size_gb = db_size_result['size_gb']
                    
                    # Get connection count
                    conn_count = self.db.execute_query("""
                        SELECT COUNT(*) as count FROM pg_stat_activity 
                        WHERE datname = current_database()
                    """, fetch='one')
                    
                    health_status['database_metrics'] = {
                        'size_gb': round(db_size_gb, 2),
                        'connections': conn_count['count'],
                        'connectivity': True
                    }
                    
                    # Check database thresholds
                    if db_size_gb >= self.config['thresholds']['database_size_critical_gb']:
                        issue = {'type': 'critical', 'metric': 'database_size', 'value': db_size_gb}
                        health_status['issues'].append(issue)
                        health_status['overall_status'] = 'critical'
                    elif db_size_gb >= self.config['thresholds']['database_size_warning_gb']:
                        issue = {'type': 'warning', 'metric': 'database_size', 'value': db_size_gb}
                        health_status['issues'].append(issue)
                        if health_status['overall_status'] == 'healthy':
                            health_status['overall_status'] = 'warning'
                
                else:
                    health_status['database_metrics']['connectivity'] = False
                    issue = {'type': 'critical', 'metric': 'database_connectivity', 'value': False}
                    health_status['issues'].append(issue)
                    health_status['overall_status'] = 'critical'
            
            except Exception as e:
                health_status['database_metrics']['connectivity'] = False
                health_status['database_metrics']['error'] = str(e)
                issue = {'type': 'critical', 'metric': 'database_error', 'value': str(e)}
                health_status['issues'].append(issue)
                health_status['overall_status'] = 'critical'
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status['overall_status'] = 'critical'
            health_status['issues'].append({'type': 'critical', 'metric': 'health_check_error', 'value': str(e)})
        
        return health_status
    
    def check_data_freshness(self) -> Dict:
        """Check if data imports are up to date"""
        freshness_status = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'dealer_status': {},
            'issues': []
        }
        
        try:
            # Check last import times for active dealerships
            import_status = self.db.execute_query("""
                SELECT 
                    d.name as dealership,
                    d.is_active,
                    MAX(r.import_date) as last_import,
                    COUNT(r.id) as records_last_7_days,
                    EXTRACT(EPOCH FROM (CURRENT_DATE - MAX(r.import_date))) / 3600 as hours_since_import
                FROM dealership_configs d
                LEFT JOIN raw_vehicle_data r ON d.name = r.location 
                    AND r.import_date >= CURRENT_DATE - INTERVAL '7 days'
                WHERE d.is_active = true
                GROUP BY d.name, d.is_active
            """)
            
            for dealer in import_status:
                dealer_name = dealer['dealership']
                hours_since = dealer['hours_since_import'] or 999  # Default to high number if no imports
                
                status = 'healthy'
                if hours_since >= self.config['thresholds']['import_delay_critical_hours']:
                    status = 'critical'
                    freshness_status['overall_status'] = 'critical'
                    freshness_status['issues'].append({
                        'type': 'critical',
                        'dealership': dealer_name,
                        'metric': 'import_delay',
                        'hours_since_import': hours_since
                    })
                elif hours_since >= self.config['thresholds']['import_delay_warning_hours']:
                    status = 'warning'
                    if freshness_status['overall_status'] == 'healthy':
                        freshness_status['overall_status'] = 'warning'
                    freshness_status['issues'].append({
                        'type': 'warning',
                        'dealership': dealer_name,
                        'metric': 'import_delay',
                        'hours_since_import': hours_since
                    })
                
                freshness_status['dealer_status'][dealer_name] = {
                    'status': status,
                    'last_import': dealer['last_import'].isoformat() if dealer['last_import'] else None,
                    'hours_since_import': round(hours_since, 1),
                    'records_last_7_days': dealer['records_last_7_days']
                }
        
        except Exception as e:
            logger.error(f"Data freshness check failed: {e}")
            freshness_status['overall_status'] = 'critical'
            freshness_status['issues'].append({'type': 'critical', 'metric': 'freshness_check_error', 'value': str(e)})
        
        return freshness_status
    
    def check_data_quality(self) -> Dict:
        """Check data quality metrics"""
        quality_status = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'metrics': {},
            'issues': []
        }
        
        try:
            # Check recent import quality
            today_imports = self.db.execute_query("""
                SELECT 
                    location,
                    COUNT(*) as total_records,
                    COUNT(*) FILTER (WHERE vin IS NULL OR LENGTH(vin) != 17) as invalid_vins,
                    COUNT(*) FILTER (WHERE stock IS NULL OR stock = '') as missing_stocks,
                    COUNT(*) FILTER (WHERE price IS NULL OR price <= 0 OR price > 500000) as invalid_prices
                FROM raw_vehicle_data
                WHERE import_date = CURRENT_DATE
                GROUP BY location
            """)
            
            for dealer_data in today_imports:
                dealer = dealer_data['location']
                invalid_vins = dealer_data['invalid_vins']
                missing_stocks = dealer_data['missing_stocks']
                invalid_prices = dealer_data['invalid_prices']
                
                quality_status['metrics'][dealer] = {
                    'total_records': dealer_data['total_records'],
                    'invalid_vins': invalid_vins,
                    'missing_stocks': missing_stocks,
                    'invalid_prices': invalid_prices
                }
                
                # Check thresholds
                if invalid_vins > self.config['data_quality']['max_missing_vins_per_import']:
                    quality_status['issues'].append({
                        'type': 'warning',
                        'dealership': dealer,
                        'metric': 'invalid_vins',
                        'count': invalid_vins
                    })
                    if quality_status['overall_status'] == 'healthy':
                        quality_status['overall_status'] = 'warning'
                
                if invalid_prices > self.config['data_quality']['max_invalid_prices_per_import']:
                    quality_status['issues'].append({
                        'type': 'warning',
                        'dealership': dealer,
                        'metric': 'invalid_prices',
                        'count': invalid_prices
                    })
                    if quality_status['overall_status'] == 'healthy':
                        quality_status['overall_status'] = 'warning'
            
            # Check for duplicate VINs
            duplicate_vins = self.db.execute_query("""
                SELECT 
                    location,
                    COUNT(*) as duplicate_count
                FROM (
                    SELECT vin, location, COUNT(*) as vin_count
                    FROM normalized_vehicle_data
                    WHERE last_seen_date >= CURRENT_DATE - INTERVAL '1 day'
                    GROUP BY vin, location
                    HAVING COUNT(*) > 1
                ) duplicates
                GROUP BY location
            """)
            
            for dup_data in duplicate_vins:
                dealer = dup_data['location']
                dup_count = dup_data['duplicate_count']
                
                if dup_count > self.config['data_quality']['max_duplicate_vins_per_dealer']:
                    quality_status['issues'].append({
                        'type': 'warning',
                        'dealership': dealer,
                        'metric': 'duplicate_vins',
                        'count': dup_count
                    })
                    if quality_status['overall_status'] == 'healthy':
                        quality_status['overall_status'] = 'warning'
        
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
            quality_status['overall_status'] = 'critical'
            quality_status['issues'].append({'type': 'critical', 'metric': 'quality_check_error', 'value': str(e)})
        
        return quality_status
    
    def send_alert(self, alert_type: str, subject: str, message: str, details: Dict = None):
        """Send alert notification"""
        if not self.config['alerting']['enabled']:
            logger.info(f"Alert (not sent): {subject}")
            return
        
        # Check cooldown
        cooldown = (self.config['alerting']['critical_alert_cooldown'] 
                   if alert_type == 'critical' 
                   else self.config['alerting']['alert_cooldown'])
        
        # Check if similar alert was sent recently
        alert_key = f"{alert_type}:{subject}"
        now = datetime.now()
        
        for hist in self.alert_history:
            if (hist['key'] == alert_key and 
                (now - hist['timestamp']).seconds < cooldown):
                logger.debug(f"Alert suppressed due to cooldown: {subject}")
                return
        
        try:
            # Send email alert
            smtp_config = self.config['alerting']['email']
            
            msg = MimeMultipart()
            msg['From'] = smtp_config['from_address']
            msg['To'] = ', '.join(smtp_config['to_addresses'])
            msg['Subject'] = f"[{alert_type.upper()}] Silver Fox DB: {subject}"
            
            body = f"""
Silver Fox Marketing Database Alert

Alert Type: {alert_type.upper()}
Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}
Subject: {subject}

Message:
{message}

Details:
{json.dumps(details, indent=2, default=str) if details else 'None'}

--
Silver Fox Marketing Database Monitoring System
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                if smtp_config['username']:
                    server.starttls()
                    server.login(smtp_config['username'], smtp_config['password'])
                
                server.send_message(msg)
            
            # Record alert
            self.alert_history.append({
                'key': alert_key,
                'timestamp': now,
                'type': alert_type,
                'subject': subject,
                'sent': True
            })
            
            logger.info(f"Alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            self.alert_history.append({
                'key': alert_key,
                'timestamp': now,
                'type': alert_type,
                'subject': subject,
                'sent': False,
                'error': str(e)
            })
    
    def process_health_results(self, health_results: Dict):
        """Process health check results and trigger alerts"""
        for issue in health_results.get('issues', []):
            alert_type = issue['type']
            metric = issue['metric']
            value = issue.get('value', 'N/A')
            
            if metric == 'cpu_usage':
                subject = f"High CPU Usage: {value}%"
                message = f"CPU usage has reached {value}%, which exceeds the {alert_type} threshold."
            elif metric == 'memory_usage':
                subject = f"High Memory Usage: {value}%"
                message = f"Memory usage has reached {value}%, which exceeds the {alert_type} threshold."
            elif metric == 'disk_usage':
                subject = f"High Disk Usage: {value}%"
                message = f"Disk usage has reached {value}%, which exceeds the {alert_type} threshold."
            elif metric == 'database_size':
                subject = f"Large Database Size: {value}GB"
                message = f"Database size has reached {value}GB."
            elif metric == 'database_connectivity':
                subject = "Database Connection Failed"
                message = "Unable to connect to the PostgreSQL database."
            else:
                subject = f"System Issue: {metric}"
                message = f"Issue detected with {metric}: {value}"
            
            self.send_alert(alert_type, subject, message, issue)
            
            # Auto-backup on critical issues
            if (alert_type == 'critical' and 
                self.config['backup']['auto_backup_on_critical'] and
                metric in ['database_connectivity', 'database_error']):
                try:
                    logger.info("Creating emergency backup due to critical database issue...")
                    backup_file = self.recovery_manager.maintenance.backup_database('emergency_critical_alert')
                    logger.info(f"Emergency backup created: {backup_file}")
                except Exception as e:
                    logger.error(f"Emergency backup failed: {e}")
    
    def process_freshness_results(self, freshness_results: Dict):
        """Process data freshness results and trigger alerts"""
        for issue in freshness_results.get('issues', []):
            dealership = issue.get('dealership', 'Unknown')
            hours_since = issue.get('hours_since_import', 0)
            alert_type = issue['type']
            
            subject = f"Stale Data: {dealership}"
            message = f"Dealership {dealership} has not imported data for {hours_since:.1f} hours."
            
            self.send_alert(alert_type, subject, message, issue)
    
    def process_quality_results(self, quality_results: Dict):
        """Process data quality results and trigger alerts"""
        for issue in quality_results.get('issues', []):
            dealership = issue.get('dealership', 'Unknown')
            metric = issue.get('metric', 'unknown')
            count = issue.get('count', 0)
            alert_type = issue['type']
            
            subject = f"Data Quality Issue: {dealership}"
            
            if metric == 'invalid_vins':
                message = f"Dealership {dealership} has {count} records with invalid VINs in today's import."
            elif metric == 'invalid_prices':
                message = f"Dealership {dealership} has {count} records with invalid prices in today's import."
            elif metric == 'duplicate_vins':
                message = f"Dealership {dealership} has {count} duplicate VINs in recent data."
            else:
                message = f"Data quality issue for {dealership}: {metric} = {count}"
            
            self.send_alert(alert_type, subject, message, issue)
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Production monitoring started")
        
        last_health_check = datetime.min
        last_performance_check = datetime.min
        last_consistency_check = datetime.min
        
        while not self.stop_event.is_set():
            try:
                now = datetime.now()
                
                # Basic health check (every monitoring interval)
                if (now - last_health_check).seconds >= self.config['monitoring_interval']:
                    logger.debug("Running health check...")
                    
                    # System and database health
                    health_results = self.check_system_health()
                    self.process_health_results(health_results)
                    
                    # Data freshness
                    freshness_results = self.check_data_freshness()
                    self.process_freshness_results(freshness_results)
                    
                    # Data quality
                    quality_results = self.check_data_quality()
                    self.process_quality_results(quality_results)
                    
                    # Store metrics
                    metrics_snapshot = {
                        'timestamp': now,
                        'health': health_results,
                        'freshness': freshness_results,
                        'quality': quality_results
                    }
                    self.metrics_history.append(metrics_snapshot)
                    
                    # Trim history to prevent memory growth
                    if len(self.metrics_history) > 1000:
                        self.metrics_history = self.metrics_history[-500:]
                    
                    last_health_check = now
                
                # Performance check (less frequent)
                if (now - last_performance_check).seconds >= self.config['performance_check_interval']:
                    logger.debug("Running performance check...")
                    try:
                        perf_results = self.performance_monitor.run_performance_analysis()
                        # Process performance alerts if needed
                        for rec in perf_results.get('recommendations', []):
                            if rec.startswith('HIGH:'):
                                self.send_alert('warning', 'Performance Issue', rec)
                    except Exception as e:
                        logger.error(f"Performance check failed: {e}")
                    
                    last_performance_check = now
                
                # Consistency check (least frequent)
                if (now - last_consistency_check).seconds >= self.config['consistency_check_interval']:
                    logger.debug("Running consistency check...")
                    try:
                        consistency_results = self.consistency_checker.run_full_consistency_check()
                        # Process consistency alerts
                        for issue in consistency_results.get('critical_issues', []):
                            subject = f"Data Consistency Issue: {issue['issue']}"
                            message = f"Critical consistency issue found: {issue.get('description', 'N/A')}"
                            self.send_alert('critical', subject, message, issue)
                    except Exception as e:
                        logger.error(f"Consistency check failed: {e}")
                    
                    last_consistency_check = now
                
                # Sleep for a short interval
                self.stop_event.wait(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                # Continue monitoring despite errors
                self.stop_event.wait(60)
        
        logger.info("Production monitoring stopped")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.monitoring_thread = Thread(target=self.monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Production monitoring system started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.is_running:
            logger.warning("Monitoring is not running")
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Production monitoring system stopped")
    
    def get_current_status(self) -> Dict:
        """Get current monitoring status"""
        if not self.metrics_history:
            return {'status': 'no_data', 'message': 'No monitoring data available'}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'last_check': latest_metrics['timestamp'],
            'system_health': latest_metrics['health']['overall_status'],
            'data_freshness': latest_metrics['freshness']['overall_status'],
            'data_quality': latest_metrics['quality']['overall_status'],
            'alerts_in_last_hour': len([
                alert for alert in self.alert_history
                if (datetime.now() - alert['timestamp']).seconds < 3600
            ])
        }
    
    def save_monitoring_config(self, filename: str = None):
        """Save current monitoring configuration"""
        if not filename:
            filename = os.path.join(config.base_path, 'monitoring_config.json')
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Monitoring configuration saved to {filename}")

def main():
    """Main function for production monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production database monitoring')
    parser.add_argument('--config', help='Monitoring configuration file')
    parser.add_argument('--start', action='store_true', help='Start monitoring daemon')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--health-check', action='store_true', help='Run single health check')
    parser.add_argument('--save-config', help='Save default config to file')
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor(args.config)
    
    try:
        if args.save_config:
            monitor.save_monitoring_config(args.save_config)
            print(f"Configuration template saved to: {args.save_config}")
        
        elif args.health_check:
            print("Running health check...")
            health = monitor.check_system_health()
            freshness = monitor.check_data_freshness()
            quality = monitor.check_data_quality()
            
            print(f"\nSystem Health: {health['overall_status']}")
            print(f"Data Freshness: {freshness['overall_status']}")
            print(f"Data Quality: {quality['overall_status']}")
            
            if health['issues'] or freshness['issues'] or quality['issues']:
                print(f"\nIssues Found:")
                for issue in health['issues'] + freshness['issues'] + quality['issues']:
                    print(f"  - {issue['type'].upper()}: {issue}")
        
        elif args.status:
            status = monitor.get_current_status()
            print(f"Monitoring Status: {status['status']}")
            if status['status'] != 'no_data':
                print(f"Last Check: {status['last_check']}")
                print(f"System Health: {status['system_health']}")
                print(f"Data Freshness: {status['data_freshness']}")
                print(f"Data Quality: {status['data_quality']}")
                print(f"Recent Alerts: {status['alerts_in_last_hour']}")
        
        elif args.start:
            print("Starting production monitoring...")
            monitor.start_monitoring()
            
            try:
                # Keep the main thread alive
                while monitor.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitor.stop_monitoring()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Monitoring failed: {e}")
        raise

if __name__ == "__main__":
    main()