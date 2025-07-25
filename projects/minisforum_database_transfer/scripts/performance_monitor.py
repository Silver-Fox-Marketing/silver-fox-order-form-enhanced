"""
Performance monitoring and benchmarking for Silver Fox Marketing dealership database
Tracks database performance metrics and identifies optimization opportunities
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from database_connection import db_manager
from database_config import config

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Database performance monitoring and benchmarking"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.metrics = {
            'timestamp': None,
            'system_metrics': {},
            'database_metrics': {},
            'query_performance': {},
            'connection_metrics': {},
            'recommendations': []
        }
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        logger.info("Collecting system metrics...")
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
        
        # Network metrics (if applicable)
        network = psutil.net_io_counters()
        
        return {
            'cpu': {
                'usage_percent': cpu_percent,
                'core_count': cpu_count,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'usage_percent': round((disk.used / disk.total) * 100, 2)
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        }
    
    def get_database_metrics(self) -> Dict:
        """Get PostgreSQL database metrics"""
        logger.info("Collecting database metrics...")
        
        # Database size
        db_size = self.db.execute_query("""
            SELECT 
                pg_database_size(current_database()) as size_bytes,
                pg_size_pretty(pg_database_size(current_database())) as size_pretty
        """, fetch='one')
        
        # Table statistics
        table_stats = self.db.execute_query("""
            SELECT 
                schemaname,
                tablename,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        # Index usage statistics
        index_stats = self.db.execute_query("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE idx_scan > 0
            ORDER BY idx_scan DESC
            LIMIT 20
        """)
        
        # Connection statistics
        connection_stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_connections,
                COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
            FROM pg_stat_activity
            WHERE datname = current_database()
        """, fetch='one')
        
        # Lock statistics
        lock_stats = self.db.execute_query("""
            SELECT 
                mode,
                COUNT(*) as count
            FROM pg_locks
            WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
            GROUP BY mode
            ORDER BY count DESC
        """)
        
        # Recent activity
        recent_activity = self.db.execute_query("""
            SELECT 
                query_start,
                state,
                LEFT(query, 100) as query_preview
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND state != 'idle'
            AND query NOT LIKE '%pg_stat_activity%'
            ORDER BY query_start DESC
            LIMIT 10
        """)
        
        return {
            'database_size': {
                'bytes': db_size['size_bytes'],
                'human_readable': db_size['size_pretty']
            },
            'tables': table_stats,
            'indexes': index_stats,
            'connections': connection_stats,
            'locks': lock_stats,
            'recent_activity': recent_activity
        }
    
    def benchmark_queries(self) -> Dict:
        """Benchmark critical queries for Silver Fox operations"""
        logger.info("Benchmarking critical queries...")
        
        # Define critical queries for Silver Fox operations
        benchmark_queries = [
            {
                'name': 'daily_import_summary',
                'description': 'Summary of daily imports by dealership',
                'sql': """
                    SELECT 
                        location,
                        import_date,
                        COUNT(*) as vehicle_count,
                        COUNT(DISTINCT vin) as unique_vins
                    FROM raw_vehicle_data
                    WHERE import_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY location, import_date
                    ORDER BY import_date DESC, location
                """,
                'target_time': 2.0
            },
            {
                'name': 'current_inventory_export',
                'description': 'Current inventory for export (typical daily operation)',
                'sql': """
                    SELECT 
                        n.vin,
                        n.stock,
                        n.year,
                        n.make,
                        n.model,
                        n.trim,
                        n.price,
                        n.vehicle_condition,
                        d.qr_output_path || n.stock || '.png' as qr_code_path
                    FROM normalized_vehicle_data n
                    JOIN dealership_configs d ON n.location = d.name
                    WHERE n.vehicle_condition IN ('new', 'po', 'cpo', 'onlot')
                    AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND d.is_active = true
                    ORDER BY n.make, n.model
                    LIMIT 5000
                """,
                'target_time': 3.0
            },
            {
                'name': 'duplicate_vin_detection',
                'description': 'Find VINs appearing at multiple dealerships',
                'sql': """
                    WITH vin_counts AS (
                        SELECT 
                            vin,
                            COUNT(DISTINCT location) as dealer_count,
                            array_agg(DISTINCT location) as dealers
                        FROM normalized_vehicle_data
                        WHERE last_seen_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY vin
                        HAVING COUNT(DISTINCT location) > 1
                    )
                    SELECT 
                        vc.vin,
                        vc.dealer_count,
                        vc.dealers,
                        n.make,
                        n.model,
                        n.year,
                        n.price
                    FROM vin_counts vc
                    JOIN normalized_vehicle_data n ON vc.vin = n.vin
                    WHERE n.last_seen_date = (
                        SELECT MAX(last_seen_date)
                        FROM normalized_vehicle_data n2
                        WHERE n2.vin = n.vin
                    )
                    ORDER BY vc.dealer_count DESC
                    LIMIT 100
                """,
                'target_time': 5.0
            },
            {
                'name': 'dealership_performance_metrics',
                'description': 'Performance metrics by dealership',
                'sql': """
                    SELECT 
                        n.location,
                        COUNT(*) as total_vehicles,
                        COUNT(DISTINCT n.vin) as unique_vins,
                        AVG(n.price) as avg_price,
                        COUNT(*) FILTER (WHERE n.vehicle_condition = 'new') as new_count,
                        COUNT(*) FILTER (WHERE n.vehicle_condition = 'po') as used_count,
                        COUNT(*) FILTER (WHERE n.vehicle_condition = 'cpo') as cpo_count,
                        MAX(r.import_date) as last_import
                    FROM normalized_vehicle_data n
                    LEFT JOIN raw_vehicle_data r ON n.vin = r.vin AND n.location = r.location
                    WHERE n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY n.location
                    ORDER BY total_vehicles DESC
                """,
                'target_time': 4.0
            },
            {
                'name': 'inventory_age_analysis',
                'description': 'Analyze how long vehicles stay in inventory',
                'sql': """
                    SELECT 
                        location,
                        vehicle_condition,
                        make,
                        AVG(EXTRACT(days FROM (CURRENT_DATE - date_in_stock))) as avg_days_in_stock,
                        COUNT(*) as vehicle_count
                    FROM normalized_vehicle_data
                    WHERE date_in_stock IS NOT NULL
                    AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND date_in_stock >= CURRENT_DATE - INTERVAL '365 days'
                    GROUP BY location, vehicle_condition, make
                    HAVING COUNT(*) >= 5
                    ORDER BY avg_days_in_stock DESC
                    LIMIT 50
                """,
                'target_time': 3.0
            }
        ]
        
        results = []
        
        for query_info in benchmark_queries:
            logger.info(f"Benchmarking: {query_info['name']}")
            
            times = []
            row_counts = []
            
            # Run each query 3 times to get average
            for run in range(3):
                start_time = time.time()
                try:
                    result = self.db.execute_query(query_info['sql'])
                    execution_time = time.time() - start_time
                    times.append(execution_time)
                    row_counts.append(len(result) if isinstance(result, list) else 1)
                except Exception as e:
                    logger.error(f"Query {query_info['name']} failed: {e}")
                    times.append(float('inf'))
                    row_counts.append(0)
            
            avg_time = sum(times) / len(times) if times else 0
            avg_rows = sum(row_counts) / len(row_counts) if row_counts else 0
            
            results.append({
                'name': query_info['name'],
                'description': query_info['description'],
                'avg_execution_time': round(avg_time, 3),
                'target_time': query_info['target_time'],
                'performance_ratio': round(avg_time / query_info['target_time'], 2) if query_info['target_time'] > 0 else 0,
                'avg_rows_returned': int(avg_rows),
                'passed': avg_time <= query_info['target_time'],
                'all_times': [round(t, 3) for t in times]
            })
        
        return {
            'queries_benchmarked': len(results),
            'passed_benchmarks': sum(1 for r in results if r['passed']),
            'results': results
        }
    
    def analyze_slow_queries(self) -> Dict:
        """Analyze slow queries if pg_stat_statements is available"""
        logger.info("Analyzing slow queries...")
        
        try:
            # Check if pg_stat_statements extension is available
            extension_check = self.db.execute_query("""
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            """, fetch='one')
            
            if not extension_check:
                return {
                    'available': False,
                    'message': 'pg_stat_statements extension not installed'
                }
            
            # Get slow queries
            slow_queries = self.db.execute_query("""
                SELECT 
                    LEFT(query, 100) as query_preview,
                    calls,
                    total_exec_time / 1000 as total_time_seconds,
                    mean_exec_time / 1000 as avg_time_seconds,
                    max_exec_time / 1000 as max_time_seconds,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) as hit_percent
                FROM pg_stat_statements
                WHERE calls > 5
                ORDER BY total_exec_time DESC
                LIMIT 20
            """)
            
            return {
                'available': True,
                'slow_queries': slow_queries
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_connection_pool_metrics(self) -> Dict:
        """Get connection pool performance metrics"""
        logger.info("Analyzing connection pool performance...")
        
        try:
            pool = self.db._connection_pool
            
            return {
                'min_connections': pool.minconn,
                'max_connections': pool.maxconn,
                'current_connections': len(pool._pool),
                'available_connections': len([c for c in pool._pool if not pool._used.get(c, False)]),
                'used_connections': len([c for c in pool._pool if pool._used.get(c, False)])
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        # System resource recommendations
        system = self.metrics.get('system_metrics', {})
        if system.get('memory', {}).get('usage_percent', 0) > 80:
            recommendations.append("HIGH: Memory usage is above 80%. Consider increasing system RAM or optimizing queries.")
        
        if system.get('cpu', {}).get('usage_percent', 0) > 70:
            recommendations.append("MEDIUM: CPU usage is consistently high. Monitor for resource-intensive queries.")
        
        if system.get('disk', {}).get('usage_percent', 0) > 85:
            recommendations.append("HIGH: Disk usage is above 85%. Clean up old data or expand storage.")
        
        # Database recommendations
        db_metrics = self.metrics.get('database_metrics', {})
        
        # Check for tables with high dead tuple ratio
        tables = db_metrics.get('tables', [])
        for table in tables:
            dead_ratio = 0
            if table['live_rows'] > 0:
                dead_ratio = table['dead_rows'] / table['live_rows']
            
            if dead_ratio > 0.1:  # More than 10% dead tuples
                recommendations.append(f"MEDIUM: Table {table['tablename']} has {dead_ratio:.1%} dead tuples. Run VACUUM.")
        
        # Check for unused indexes
        indexes = db_metrics.get('indexes', [])
        for index in indexes:
            if index['scans'] < 10:  # Less than 10 scans
                recommendations.append(f"LOW: Index {index['indexname']} is rarely used. Consider dropping it.")
        
        # Query performance recommendations
        query_perf = self.metrics.get('query_performance', {})
        results = query_perf.get('results', [])
        
        for result in results:
            if not result['passed']:
                ratio = result['performance_ratio']
                if ratio > 2:
                    recommendations.append(f"HIGH: Query '{result['name']}' is {ratio}x slower than target. Needs optimization.")
                elif ratio > 1.5:
                    recommendations.append(f"MEDIUM: Query '{result['name']}' is {ratio}x slower than target.")
        
        # Connection pool recommendations
        conn_metrics = self.metrics.get('connection_metrics', {})
        if 'used_connections' in conn_metrics and 'max_connections' in conn_metrics:
            usage_ratio = conn_metrics['used_connections'] / conn_metrics['max_connections']
            if usage_ratio > 0.8:
                recommendations.append("MEDIUM: Connection pool usage is high. Consider increasing pool size.")
        
        return recommendations
    
    def run_performance_analysis(self) -> Dict:
        """Run complete performance analysis"""
        self.metrics['timestamp'] = datetime.now()
        
        logger.info("Starting comprehensive performance analysis...")
        
        # Collect all metrics
        self.metrics['system_metrics'] = self.get_system_metrics()
        self.metrics['database_metrics'] = self.get_database_metrics()
        self.metrics['query_performance'] = self.benchmark_queries()
        self.metrics['connection_metrics'] = self.get_connection_pool_metrics()
        self.metrics['slow_queries'] = self.analyze_slow_queries()
        
        # Generate recommendations
        self.metrics['recommendations'] = self.generate_recommendations()
        
        return self.metrics
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.metrics['timestamp']:
            return "No performance data available. Run analysis first."
        
        report = f"""
SILVER FOX MARKETING - DATABASE PERFORMANCE REPORT
=================================================
Generated: {self.metrics['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

SYSTEM RESOURCES
================
CPU Usage: {self.metrics['system_metrics']['cpu']['usage_percent']:.1f}%
Memory Usage: {self.metrics['system_metrics']['memory']['usage_percent']:.1f}% ({self.metrics['system_metrics']['memory']['used_gb']:.1f}GB / {self.metrics['system_metrics']['memory']['total_gb']:.1f}GB)
Disk Usage: {self.metrics['system_metrics']['disk']['usage_percent']:.1f}% ({self.metrics['system_metrics']['disk']['used_gb']:.1f}GB / {self.metrics['system_metrics']['disk']['total_gb']:.1f}GB)

DATABASE METRICS
================
Database Size: {self.metrics['database_metrics']['database_size']['human_readable']}
Active Connections: {self.metrics['database_metrics']['connections']['active_connections']}
Total Connections: {self.metrics['database_metrics']['connections']['total_connections']}

TABLE STATISTICS (Top 5 by size)
---------------------------------
"""
        
        tables = self.metrics['database_metrics']['tables'][:5]
        for table in tables:
            report += f"{table['tablename']:25} | {table['table_size']:>10} | {table['live_rows']:>10,} rows\n"
        
        report += f"""
QUERY PERFORMANCE BENCHMARKS
=============================
Queries Benchmarked: {self.metrics['query_performance']['queries_benchmarked']}
Passed Benchmarks: {self.metrics['query_performance']['passed_benchmarks']}

Query Results:
"""
        
        for result in self.metrics['query_performance']['results']:
            status = "PASS" if result['passed'] else "FAIL"
            report += f"  {result['name']:30} | {result['avg_execution_time']:>6.3f}s | {status}\n"
        
        report += f"""
RECOMMENDATIONS ({len(self.metrics['recommendations'])})
===============
"""
        
        if self.metrics['recommendations']:
            for i, rec in enumerate(self.metrics['recommendations'], 1):
                report += f"{i}. {rec}\n"
        else:
            report += "✅ No performance issues detected.\n"
        
        # Connection pool status
        conn_metrics = self.metrics['connection_metrics']
        if 'error' not in conn_metrics:
            report += f"""
CONNECTION POOL STATUS
======================
Pool Size: {conn_metrics['current_connections']} / {conn_metrics['max_connections']}
Available: {conn_metrics['available_connections']}
In Use: {conn_metrics['used_connections']}
"""
        
        return report
    
    def save_metrics_history(self, filename: str = None):
        """Save metrics to JSON file for historical tracking"""
        if not filename:
            timestamp = self.metrics['timestamp'].strftime('%Y%m%d_%H%M%S')
            filename = f"performance_metrics_{timestamp}.json"
        
        filepath = os.path.join(config.base_path, 'monitoring', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        metrics_copy = json.loads(json.dumps(self.metrics, default=str))
        
        with open(filepath, 'w') as f:
            json.dump(metrics_copy, f, indent=2)
        
        logger.info(f"Performance metrics saved to {filepath}")
        return filepath

def main():
    """Main function for command-line performance monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database performance monitoring')
    parser.add_argument('--analyze', action='store_true', help='Run full performance analysis')
    parser.add_argument('--benchmark', action='store_true', help='Run query benchmarks only')
    parser.add_argument('--system', action='store_true', help='Show system metrics only')
    parser.add_argument('--database', action='store_true', help='Show database metrics only')
    parser.add_argument('--save', help='Save results to file')
    parser.add_argument('--report', help='Generate report file')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    try:
        if args.analyze or not any([args.benchmark, args.system, args.database]):
            print("Running comprehensive performance analysis...")
            results = monitor.run_performance_analysis()
            
            # Display summary
            print(f"\nPerformance Analysis Complete")
            print(f"System Memory: {results['system_metrics']['memory']['usage_percent']:.1f}%")
            print(f"Database Size: {results['database_metrics']['database_size']['human_readable']}")
            print(f"Query Benchmarks: {results['query_performance']['passed_benchmarks']}/{results['query_performance']['queries_benchmarked']} passed")
            print(f"Recommendations: {len(results['recommendations'])}")
            
        elif args.benchmark:
            print("Running query benchmarks...")
            results = monitor.benchmark_queries()
            print(f"Benchmarked {results['queries_benchmarked']} queries")
            print(f"Passed: {results['passed_benchmarks']}")
            
        elif args.system:
            print("Collecting system metrics...")
            results = monitor.get_system_metrics()
            print(f"CPU: {results['cpu']['usage_percent']:.1f}%")
            print(f"Memory: {results['memory']['usage_percent']:.1f}%")
            print(f"Disk: {results['disk']['usage_percent']:.1f}%")
            
        elif args.database:
            print("Collecting database metrics...")
            results = monitor.get_database_metrics()
            print(f"Database Size: {results['database_size']['human_readable']}")
            print(f"Active Connections: {results['connections']['active_connections']}")
        
        # Generate and save report
        if args.report:
            report = monitor.generate_performance_report()
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.report}")
        
        # Save metrics
        if args.save:
            filepath = monitor.save_metrics_history(args.save)
            print(f"Metrics saved to: {filepath}")
    
    except Exception as e:
        print(f"Performance monitoring failed: {e}")
        raise

if __name__ == "__main__":
    main()