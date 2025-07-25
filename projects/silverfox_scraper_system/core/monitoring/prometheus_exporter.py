#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for Silver Fox Scraper System
=========================================================

Custom Prometheus exporter that collects and exposes business-specific
metrics for the Silver Fox scraper system including inventory, pricing,
performance, and operational metrics.

Author: Claude (Silver Fox Assistant)  
Created: July 2025
"""

import time
import threading
import logging
import json
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Summary, Info
from prometheus_client.core import CollectorRegistry
import psutil
import requests
from dataclasses import dataclass


@dataclass
class MetricDefinition:
    """Definition of a custom metric"""
    name: str
    description: str
    metric_type: str  # gauge, counter, histogram, summary, info
    labels: List[str]


class SilverFoxMetricsCollector:
    """Custom metrics collector for Silver Fox scraper system"""
    
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SilverFoxMetricsCollector")
        
        # Initialize metrics registry
        self.registry = CollectorRegistry()
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Metric collection state
        self.last_collection_time = time.time()
        self.collection_errors = 0
    
    def _initialize_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # System health metrics
        self.system_health = Gauge(
            'silverfox_system_health_status',
            'Overall system health status (1=healthy, 0=unhealthy)',
            ['component'],
            registry=self.registry
        )
        
        # Inventory metrics
        self.total_inventory = Gauge(
            'silverfox_total_inventory_count',
            'Total number of vehicles in inventory',
            ['dealership', 'location'],
            registry=self.registry
        )
        
        self.inventory_by_type = Gauge(
            'silverfox_vehicles_by_type',
            'Number of vehicles by type',
            ['dealership', 'vehicle_type', 'make', 'model'],
            registry=self.registry
        )
        
        self.inventory_value = Gauge(
            'silverfox_inventory_total_value_dollars',
            'Total value of inventory in dollars',
            ['dealership'],
            registry=self.registry
        )
        
        # Scraper performance metrics
        self.scraper_duration = Histogram(
            'silverfox_scraper_duration_seconds',
            'Time spent scraping each dealership',
            ['dealership', 'scraper_type'],
            buckets=[30, 60, 120, 300, 600, 1200],
            registry=self.registry
        )
        
        self.vehicles_scraped = Counter(
            'silverfox_vehicles_scraped_total',
            'Total number of vehicles scraped',
            ['dealership', 'scraper_type', 'status'],
            registry=self.registry
        )
        
        self.scraper_errors = Counter(
            'silverfox_scraper_errors_total',
            'Total number of scraper errors',
            ['dealership', 'error_type', 'scraper_type'],
            registry=self.registry
        )
        
        self.scraper_success_rate = Gauge(
            'silverfox_scraper_success_rate',
            'Success rate of scraper operations (0-1)',
            ['dealership', 'scraper_type'],
            registry=self.registry
        )
        
        self.last_successful_scrape = Gauge(
            'silverfox_scraper_last_success_timestamp',
            'Timestamp of last successful scrape',
            ['dealership'],
            registry=self.registry
        )
        
        # Page performance metrics
        self.page_load_time = Histogram(
            'silverfox_page_load_time_seconds',
            'Time to load dealership pages',
            ['dealership', 'page_type'],
            buckets=[1, 2, 5, 10, 20, 30],
            registry=self.registry
        )
        
        self.api_response_time = Histogram(
            'silverfox_api_response_time_seconds',
            'API response times for dealership APIs',
            ['dealership', 'api_endpoint'],
            buckets=[0.1, 0.5, 1, 2, 5, 10],
            registry=self.registry
        )
        
        # Anti-bot metrics
        self.anti_bot_delays = Summary(
            'silverfox_anti_bot_delays_seconds',
            'Time spent in anti-bot delays',
            ['dealership', 'delay_type'],
            registry=self.registry
        )
        
        self.captcha_encounters = Counter(
            'silverfox_captcha_encounters_total',
            'Number of CAPTCHA challenges encountered',
            ['dealership', 'captcha_type'],
            registry=self.registry
        )
        
        self.rate_limit_hits = Counter(
            'silverfox_rate_limit_hits_total',
            'Number of rate limit encounters',
            ['dealership', 'limit_type'],
            registry=self.registry
        )
        
        # Business intelligence metrics
        self.competitive_price_difference = Gauge(
            'silverfox_competitive_price_difference_percent',
            'Price difference vs competitors in percent',
            ['dealership', 'vehicle_model', 'competitor'],
            registry=self.registry
        )
        
        self.price_alerts_active = Gauge(
            'silverfox_price_alerts_active',
            'Number of active price alerts',
            ['dealership', 'alert_type'],
            registry=self.registry
        )
        
        self.inventory_turnover_rate = Gauge(
            'silverfox_inventory_turnover_rate',
            'Inventory turnover rate (vehicles/day)',
            ['dealership', 'vehicle_type'],
            registry=self.registry
        )
        
        self.market_share_percent = Gauge(
            'silverfox_market_share_percent',
            'Market share percentage by category',
            ['dealership', 'vehicle_category', 'geographic_area'],
            registry=self.registry
        )
        
        self.revenue_opportunity = Gauge(
            'silverfox_revenue_opportunity_dollars',
            'Estimated revenue opportunity in dollars',
            ['dealership', 'opportunity_type'],
            registry=self.registry
        )
        
        # Chrome browser metrics
        self.chrome_memory_usage = Gauge(
            'silverfox_chrome_memory_usage_bytes',
            'Chrome browser memory usage in bytes',
            ['pod', 'dealership'],
            registry=self.registry
        )
        
        self.chrome_cpu_usage = Gauge(
            'silverfox_chrome_cpu_usage_percent',
            'Chrome browser CPU usage percentage',
            ['pod', 'dealership'],
            registry=self.registry
        )
        
        self.chrome_crashes = Counter(
            'silverfox_chrome_crashes_total',
            'Number of Chrome browser crashes',
            ['pod', 'dealership', 'crash_type'],
            registry=self.registry
        )
        
        # Data quality metrics
        self.data_quality_score = Gauge(
            'silverfox_data_quality_score',
            'Data quality score (0-1)',
            ['dealership', 'data_type'],
            registry=self.registry
        )
        
        self.missing_data_fields = Gauge(
            'silverfox_missing_data_fields_count',
            'Number of missing required data fields',
            ['dealership', 'vehicle_id'],
            registry=self.registry
        )
        
        self.duplicate_vehicles_detected = Counter(
            'silverfox_duplicate_vehicles_total',
            'Number of duplicate vehicles detected',
            ['dealership', 'detection_method'],
            registry=self.registry
        )
        
        # Integration metrics
        self.pipedrive_sync_success = Gauge(
            'silverfox_pipedrive_sync_success_rate',
            'PipeDrive synchronization success rate',
            ['sync_type'],
            registry=self.registry
        )
        
        self.pipedrive_api_calls = Counter(
            'silverfox_pipedrive_api_calls_total',
            'Total PipeDrive API calls made',
            ['endpoint', 'method', 'status'],
            registry=self.registry
        )
        
        self.email_alerts_sent = Counter(
            'silverfox_email_alerts_sent_total',
            'Total email alerts sent',
            ['alert_type', 'recipient_type', 'status'],
            registry=self.registry
        )
        
        # Resource usage metrics
        self.redis_queue_depth = Gauge(
            'silverfox_redis_queue_depth',
            'Number of items in Redis queues',
            ['queue_name'],
            registry=self.registry
        )
        
        self.active_scraping_jobs = Gauge(
            'silverfox_active_scraping_jobs',
            'Number of currently active scraping jobs',
            ['job_type'],
            registry=self.registry
        )
        
        self.worker_utilization = Gauge(
            'silverfox_worker_utilization_percent',
            'Worker utilization percentage',
            ['worker_id', 'worker_type'],
            registry=self.registry
        )
        
        # Custom business metrics
        self.luxury_vehicle_ratio = Gauge(
            'silverfox_luxury_vehicle_ratio',
            'Ratio of luxury to standard vehicles',
            ['dealership'],
            registry=self.registry
        )
        
        self.average_vehicle_age_days = Gauge(
            'silverfox_average_vehicle_age_days',
            'Average age of vehicles in inventory (days)',
            ['dealership', 'vehicle_type'],
            registry=self.registry
        )
        
        self.price_trend_direction = Gauge(
            'silverfox_price_trend_direction',
            'Price trend direction (1=up, 0=stable, -1=down)',
            ['dealership', 'vehicle_model'],
            registry=self.registry
        )
        
        # Collection metadata
        self.metrics_collection_duration = Histogram(
            'silverfox_metrics_collection_duration_seconds',
            'Time spent collecting metrics',
            ['collector_type'],
            buckets=[0.1, 0.5, 1, 2, 5, 10],
            registry=self.registry
        )
        
        self.metrics_collection_errors = Counter(
            'silverfox_metrics_collection_errors_total',
            'Number of metrics collection errors',
            ['collector_type', 'error_type'],
            registry=self.registry
        )
        
        self.last_collection_timestamp = Gauge(
            'silverfox_last_metrics_collection_timestamp',
            'Timestamp of last metrics collection',
            ['collector_type'],
            registry=self.registry
        )
    
    def collect_inventory_metrics(self):
        """Collect inventory-related metrics"""
        try:
            start_time = time.time()
            
            # Get inventory data from Redis
            inventory_keys = self.redis_client.keys("inventory:*")
            
            for key in inventory_keys:
                try:
                    inventory_data = json.loads(self.redis_client.get(key))
                    dealership = inventory_data.get('dealership', 'unknown')
                    location = inventory_data.get('location', 'unknown')
                    
                    # Total inventory count
                    total_count = len(inventory_data.get('vehicles', []))
                    self.total_inventory.labels(
                        dealership=dealership,
                        location=location
                    ).set(total_count)
                    
                    # Inventory by type
                    vehicle_counts = {}
                    total_value = 0
                    
                    for vehicle in inventory_data.get('vehicles', []):
                        vehicle_type = vehicle.get('type', 'unknown')
                        make = vehicle.get('make', 'unknown')
                        model = vehicle.get('model', 'unknown')
                        
                        key = (vehicle_type, make, model)
                        vehicle_counts[key] = vehicle_counts.get(key, 0) + 1
                        
                        # Add to total value
                        price = vehicle.get('price', 0)
                        if isinstance(price, (int, float)):
                            total_value += price
                    
                    # Set vehicle type metrics
                    for (vehicle_type, make, model), count in vehicle_counts.items():
                        self.inventory_by_type.labels(
                            dealership=dealership,
                            vehicle_type=vehicle_type,
                            make=make,
                            model=model
                        ).set(count)
                    
                    # Set total inventory value
                    self.inventory_value.labels(dealership=dealership).set(total_value)
                    
                    # Calculate luxury vehicle ratio
                    luxury_types = ['luxury', 'exotic', 'supercar', 'ultra-luxury']
                    luxury_count = sum(
                        count for (vtype, _, _), count in vehicle_counts.items()
                        if any(lux in vtype.lower() for lux in luxury_types)
                    )
                    luxury_ratio = luxury_count / total_count if total_count > 0 else 0
                    self.luxury_vehicle_ratio.labels(dealership=dealership).set(luxury_ratio)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in inventory key: {key}")
                except Exception as e:
                    self.logger.error(f"Error processing inventory key {key}: {e}")
            
            # Record collection time
            duration = time.time() - start_time
            self.metrics_collection_duration.labels(collector_type='inventory').observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error collecting inventory metrics: {e}")
            self.metrics_collection_errors.labels(
                collector_type='inventory',
                error_type=type(e).__name__
            ).inc()
    
    def collect_scraper_performance_metrics(self):
        """Collect scraper performance metrics"""
        try:
            start_time = time.time()
            
            # Get scraper performance data from Redis
            perf_keys = self.redis_client.keys("scraper_perf:*")
            
            for key in perf_keys:
                try:
                    perf_data = json.loads(self.redis_client.get(key))
                    dealership = perf_data.get('dealership', 'unknown')
                    scraper_type = perf_data.get('scraper_type', 'unknown')
                    
                    # Scraper duration
                    duration = perf_data.get('duration_seconds', 0)
                    self.scraper_duration.labels(
                        dealership=dealership,
                        scraper_type=scraper_type
                    ).observe(duration)
                    
                    # Success rate
                    success_rate = perf_data.get('success_rate', 0)
                    self.scraper_success_rate.labels(
                        dealership=dealership,
                        scraper_type=scraper_type
                    ).set(success_rate)
                    
                    # Last successful scrape
                    last_success = perf_data.get('last_success_timestamp', 0)
                    self.last_successful_scrape.labels(dealership=dealership).set(last_success)
                    
                    # Vehicle counts
                    vehicles_scraped = perf_data.get('vehicles_scraped', 0)
                    status = perf_data.get('status', 'unknown')
                    self.vehicles_scraped.labels(
                        dealership=dealership,
                        scraper_type=scraper_type,
                        status=status
                    ).inc(vehicles_scraped)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in performance key: {key}")
                except Exception as e:
                    self.logger.error(f"Error processing performance key {key}: {e}")
            
            # Record collection time
            duration = time.time() - start_time
            self.metrics_collection_duration.labels(collector_type='scraper_performance').observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error collecting scraper performance metrics: {e}")
            self.metrics_collection_errors.labels(
                collector_type='scraper_performance',
                error_type=type(e).__name__
            ).inc()
    
    def collect_business_metrics(self):
        """Collect business intelligence metrics"""
        try:
            start_time = time.time()
            
            # Get competitive pricing data
            pricing_keys = self.redis_client.keys("competitive_pricing:*")
            
            for key in pricing_keys:
                try:
                    pricing_data = json.loads(self.redis_client.get(key))
                    
                    for comparison in pricing_data.get('comparisons', []):
                        dealership = comparison.get('dealership', 'unknown')
                        vehicle_model = comparison.get('vehicle_model', 'unknown')
                        competitor = comparison.get('competitor', 'unknown')
                        price_diff = comparison.get('price_difference_percent', 0)
                        
                        self.competitive_price_difference.labels(
                            dealership=dealership,
                            vehicle_model=vehicle_model,
                            competitor=competitor
                        ).set(price_diff)
                
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in pricing key: {key}")
                except Exception as e:
                    self.logger.error(f"Error processing pricing key {key}: {e}")
            
            # Get alert data
            alert_keys = self.redis_client.keys("alerts:active:*")
            alert_counts = {}
            
            for key in alert_keys:
                try:
                    alert_data = json.loads(self.redis_client.get(key))
                    dealership = alert_data.get('dealership', 'unknown')
                    alert_type = alert_data.get('alert_type', 'unknown')
                    
                    key = (dealership, alert_type)
                    alert_counts[key] = alert_counts.get(key, 0) + 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing alert key {key}: {e}")
            
            # Set alert metrics
            for (dealership, alert_type), count in alert_counts.items():
                self.price_alerts_active.labels(
                    dealership=dealership,
                    alert_type=alert_type
                ).set(count)
            
            # Record collection time
            duration = time.time() - start_time
            self.metrics_collection_duration.labels(collector_type='business').observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error collecting business metrics: {e}")
            self.metrics_collection_errors.labels(
                collector_type='business',
                error_type=type(e).__name__
            ).inc()
    
    def collect_system_metrics(self):
        """Collect system health and resource metrics"""
        try:
            start_time = time.time()
            
            # Redis queue depths
            queue_names = ['scraper_jobs', 'analysis_jobs', 'alerts', 'sync_jobs']
            for queue_name in queue_names:
                queue_depth = self.redis_client.llen(queue_name)
                self.redis_queue_depth.labels(queue_name=queue_name).set(queue_depth)
            
            # Active scraping jobs
            active_jobs = self.redis_client.scard("active_jobs")
            self.active_scraping_jobs.labels(job_type='scraper').set(active_jobs)
            
            # System health components
            components = ['redis', 'scrapers', 'analytics', 'alerts']
            for component in components:
                # This would normally check actual component health
                # For now, assume healthy if we can collect metrics
                health_status = 1 if self.redis_client.ping() else 0
                self.system_health.labels(component=component).set(health_status)
            
            # Chrome process metrics (if available)
            try:
                chrome_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                    if 'chrome' in proc.info['name'].lower():
                        chrome_processes.append(proc)
                
                for i, proc in enumerate(chrome_processes):
                    pod_name = f"chrome-{i}"
                    memory_bytes = proc.info['memory_info'].rss
                    cpu_percent = proc.info['cpu_percent']
                    
                    self.chrome_memory_usage.labels(
                        pod=pod_name,
                        dealership='system'
                    ).set(memory_bytes)
                    
                    self.chrome_cpu_usage.labels(
                        pod=pod_name,
                        dealership='system'
                    ).set(cpu_percent)
                    
            except Exception as e:
                self.logger.debug(f"Could not collect Chrome metrics: {e}")
            
            # Record collection time
            duration = time.time() - start_time
            self.metrics_collection_duration.labels(collector_type='system').observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            self.metrics_collection_errors.labels(
                collector_type='system',
                error_type=type(e).__name__
            ).inc()
    
    def collect_integration_metrics(self):
        """Collect integration-related metrics"""
        try:
            start_time = time.time()
            
            # PipeDrive sync metrics
            pipedrive_stats = self.redis_client.hgetall("pipedrive_stats")
            if pipedrive_stats:
                sync_success_rate = float(pipedrive_stats.get('success_rate', 0))
                self.pipedrive_sync_success.labels(sync_type='vehicles').set(sync_success_rate)
                
                api_calls = int(pipedrive_stats.get('api_calls_today', 0))
                self.pipedrive_api_calls.labels(
                    endpoint='vehicles',
                    method='POST',
                    status='success'
                ).inc(api_calls)
            
            # Email alert metrics
            email_stats = self.redis_client.hgetall("email_stats")
            if email_stats:
                alerts_sent = int(email_stats.get('alerts_sent_today', 0))
                self.email_alerts_sent.labels(
                    alert_type='system',
                    recipient_type='admin',
                    status='sent'
                ).inc(alerts_sent)
            
            # Record collection time
            duration = time.time() - start_time
            self.metrics_collection_duration.labels(collector_type='integration').observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error collecting integration metrics: {e}")
            self.metrics_collection_errors.labels(
                collector_type='integration',
                error_type=type(e).__name__
            ).inc()
    
    def collect_all_metrics(self):
        """Collect all metrics"""
        try:
            collection_start = time.time()
            
            # Update last collection timestamp
            self.last_collection_timestamp.labels(collector_type='all').set(collection_start)
            
            # Collect all metric types
            self.collect_inventory_metrics()
            self.collect_scraper_performance_metrics()
            self.collect_business_metrics()
            self.collect_system_metrics()
            self.collect_integration_metrics()
            
            # Update collection metadata
            self.last_collection_time = collection_start
            
            self.logger.info("Metrics collection completed successfully")
            
        except Exception as e:
            self.collection_errors += 1
            self.logger.error(f"Error in metrics collection: {e}")
            self.metrics_collection_errors.labels(
                collector_type='all',
                error_type=type(e).__name__
            ).inc()


class PrometheusExporter:
    """Main Prometheus exporter for Silver Fox system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PrometheusExporter")
        
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            password=config['redis'].get('password'),
            decode_responses=True
        )
        
        # Initialize metrics collector
        self.metrics_collector = SilverFoxMetricsCollector(self.redis_client, config)
        
        # Collection settings
        self.collection_interval = config.get('collection_interval', 30)  # seconds
        self.http_port = config.get('http_port', 9090)
        
        # Control flags
        self.running = False
        self.collection_thread = None
    
    def start_collection_loop(self):
        """Start the metrics collection loop in a separate thread"""
        def collection_loop():
            while self.running:
                try:
                    self.metrics_collector.collect_all_metrics()
                    time.sleep(self.collection_interval)
                except Exception as e:
                    self.logger.error(f"Error in collection loop: {e}")
                    time.sleep(5)  # Short delay before retrying
        
        self.running = True
        self.collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self.collection_thread.start()
        self.logger.info(f"Started metrics collection loop (interval: {self.collection_interval}s)")
    
    def start_http_server(self):
        """Start the HTTP server for Prometheus to scrape"""
        try:
            start_http_server(self.http_port, registry=self.metrics_collector.registry)
            self.logger.info(f"Prometheus HTTP server started on port {self.http_port}")
        except Exception as e:
            self.logger.error(f"Failed to start HTTP server: {e}")
            raise
    
    def start(self):
        """Start the complete Prometheus exporter"""
        try:
            # Test Redis connection
            self.redis_client.ping()
            self.logger.info("Redis connection successful")
            
            # Start HTTP server
            self.start_http_server()
            
            # Start collection loop
            self.start_collection_loop()
            
            self.logger.info("Silver Fox Prometheus exporter started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus exporter: {e}")
            raise
    
    def stop(self):
        """Stop the Prometheus exporter"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        self.logger.info("Silver Fox Prometheus exporter stopped")
    
    def health_check(self) -> Dict[str, Any]:
        """Return health check information"""
        try:
            redis_healthy = self.redis_client.ping()
            collection_lag = time.time() - self.metrics_collector.last_collection_time
            
            return {
                "status": "healthy" if redis_healthy and collection_lag < 120 else "unhealthy",
                "redis_connection": "ok" if redis_healthy else "failed",
                "last_collection_seconds_ago": collection_lag,
                "collection_errors": self.metrics_collector.collection_errors,
                "uptime_seconds": time.time() - self.metrics_collector.last_collection_time
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


def main():
    """Main entry point for the Prometheus exporter"""
    import argparse
    import signal
    import sys
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Silver Fox Prometheus Exporter")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--redis-password", default=None, help="Redis password")
    parser.add_argument("--http-port", type=int, default=9090, help="HTTP server port")
    parser.add_argument("--collection-interval", type=int, default=30, help="Collection interval in seconds")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = {
        'redis': {
            'host': args.redis_host,
            'port': args.redis_port,
            'password': args.redis_password
        },
        'http_port': args.http_port,
        'collection_interval': args.collection_interval
    }
    
    # Create and start exporter
    exporter = PrometheusExporter(config)
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print("\nShutting down Prometheus exporter...")
        exporter.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        exporter.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        logging.error(f"Exporter failed: {e}")
        sys.exit(1)
    finally:
        exporter.stop()


if __name__ == "__main__":
    main()