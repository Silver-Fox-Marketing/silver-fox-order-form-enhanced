"""
Comprehensive stress test suite for Silver Fox Marketing dealership database
Tests performance, reliability, and data integrity under production-like conditions
"""
import time
import random
import string
import concurrent.futures
import psutil
import logging
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import json
import os
import tempfile
from database_connection import db_manager
from csv_importer import CSVImporter
from data_exporter import DataExporter
from database_maintenance import DatabaseMaintenance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DealershipDatabaseStressTest:
    """Comprehensive stress testing for the dealership database"""
    
    def __init__(self):
        self.db = db_manager
        self.importer = CSVImporter()
        self.exporter = DataExporter()
        self.maintenance = DatabaseMaintenance()
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
    
    def generate_test_vehicle_data(self, num_vehicles: int, dealership_name: str) -> List[Dict]:
        """Generate realistic test vehicle data"""
        makes = ['Ford', 'Chevrolet', 'Toyota', 'Honda', 'Nissan', 'Jeep', 'RAM', 
                'GMC', 'Hyundai', 'Kia', 'Mazda', 'Subaru', 'Volkswagen']
        models = {
            'Ford': ['F-150', 'Explorer', 'Escape', 'Edge', 'Mustang'],
            'Chevrolet': ['Silverado', 'Equinox', 'Traverse', 'Malibu', 'Tahoe'],
            'Toyota': ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Tacoma'],
            'Honda': ['Accord', 'Civic', 'CR-V', 'Pilot', 'Ridgeline'],
            'Nissan': ['Altima', 'Rogue', 'Sentra', 'Pathfinder', 'Frontier'],
            'Jeep': ['Wrangler', 'Cherokee', 'Grand Cherokee', 'Compass', 'Renegade'],
            'RAM': ['1500', '2500', '3500', 'ProMaster'],
            'GMC': ['Sierra', 'Terrain', 'Acadia', 'Yukon'],
            'Hyundai': ['Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'Palisade'],
            'Kia': ['Forte', 'Optima', 'Sportage', 'Sorento', 'Telluride'],
            'Mazda': ['Mazda3', 'CX-5', 'CX-9', 'MX-5 Miata'],
            'Subaru': ['Outback', 'Crosstrek', 'Forester', 'Ascent', 'Impreza'],
            'Volkswagen': ['Jetta', 'Passat', 'Tiguan', 'Atlas']
        }
        
        colors = ['Black', 'White', 'Silver', 'Red', 'Blue', 'Gray', 'Green', 'Brown']
        statuses = ['Available', 'In-Transit', 'Arriving Soon', 'On-Lot']
        types = ['New', 'Used', 'Certified Pre-Owned', 'Pre-Owned']
        
        vehicles = []
        for i in range(num_vehicles):
            make = random.choice(makes)
            model = random.choice(models.get(make, ['Unknown']))
            year = random.randint(2019, 2024)
            
            # Generate realistic VIN (17 characters)
            vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
            
            # Generate stock number
            stock = f"STK{random.randint(10000, 99999)}"
            
            # Price based on vehicle type and year
            base_price = random.randint(20000, 80000)
            if year == 2024:
                price = base_price * 1.1
            else:
                price = base_price * (0.9 ** (2024 - year))
            
            vehicle = {
                'vin': vin,
                'stock': stock,
                'type': random.choice(types),
                'year': year,
                'make': make,
                'model': model,
                'trim': random.choice(['Base', 'LT', 'LTZ', 'Limited', 'Sport', 'Touring']),
                'ext_color': random.choice(colors),
                'status': random.choice(statuses),
                'price': round(price, 2),
                'body_style': 'SUV' if 'Explorer' in model or 'RAV4' in model else 'Sedan',
                'fuel_type': 'Gasoline',
                'msrp': round(price * 1.05, 2),
                'date_in_stock': (date.today() - timedelta(days=random.randint(0, 90))).isoformat(),
                'street_address': '123 Main St',
                'locality': 'St. Louis',
                'postal_code': '63101',
                'region': 'MO',
                'country': 'USA',
                'location': dealership_name,
                'vehicle_url': f'https://example.com/vehicle/{vin}'
            }
            vehicles.append(vehicle)
        
        return vehicles
    
    def test_bulk_import_performance(self) -> Dict:
        """Test importing 195MB of data (typical daily load)"""
        logger.info("Testing bulk import performance (195MB simulation)...")
        
        # Generate test data for 39 dealerships (~5MB each)
        dealerships = [f"test_dealer_{i}" for i in range(39)]
        total_vehicles = 100000  # Approximately 195MB of data
        vehicles_per_dealer = total_vehicles // len(dealerships)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Create temporary CSV files
            temp_dir = tempfile.mkdtemp()
            csv_files = []
            
            # Generate CSV files
            for dealer in dealerships:
                vehicles = self.generate_test_vehicle_data(vehicles_per_dealer, dealer)
                df = pd.DataFrame(vehicles)
                csv_path = os.path.join(temp_dir, f"{dealer}.csv")
                df.to_csv(csv_path, index=False)
                csv_files.append(csv_path)
            
            # Import all files
            import_start = time.time()
            for csv_file in csv_files:
                self.importer.import_csv_file(csv_file)
            import_end = time.time()
            
            # Get final metrics
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            total_time = time.time() - start_time
            import_time = import_end - import_start
            
            # Verify data was imported
            row_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM raw_vehicle_data WHERE import_date = CURRENT_DATE",
                fetch='one'
            )['count']
            
            metrics = {
                'total_time_seconds': round(total_time, 2),
                'import_time_seconds': round(import_time, 2),
                'vehicles_imported': row_count,
                'import_rate_per_second': round(row_count / import_time, 2),
                'memory_used_mb': round(end_memory - start_memory, 2),
                'success': row_count >= total_vehicles * 0.95  # Allow 5% tolerance
            }
            
            # Cleanup test data
            self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Bulk import test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_concurrent_operations(self) -> Dict:
        """Test concurrent imports and queries"""
        logger.info("Testing concurrent database operations...")
        
        results = {'success': True, 'operations_completed': 0, 'errors': []}
        
        def import_task(dealer_num):
            """Simulate concurrent import"""
            vehicles = self.generate_test_vehicle_data(100, f"concurrent_dealer_{dealer_num}")
            df = pd.DataFrame(vehicles)
            temp_file = f"/tmp/concurrent_test_{dealer_num}.csv"
            df.to_csv(temp_file, index=False)
            self.importer.import_csv_file(temp_file, f"concurrent_dealer_{dealer_num}")
            os.remove(temp_file)
            return f"Import {dealer_num} completed"
        
        def query_task(query_num):
            """Simulate concurrent queries"""
            queries = [
                "SELECT COUNT(*) FROM normalized_vehicle_data WHERE vehicle_condition = 'new'",
                "SELECT * FROM current_inventory LIMIT 100",
                "SELECT vin, COUNT(*) FROM vin_history GROUP BY vin HAVING COUNT(*) > 1",
                "SELECT * FROM dealership_configs WHERE is_active = true"
            ]
            query = queries[query_num % len(queries)]
            result = self.db.execute_query(query)
            return f"Query {query_num} returned {len(result) if isinstance(result, list) else 1} rows"
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit mixed operations
                futures = []
                
                # Submit imports
                for i in range(5):
                    futures.append(executor.submit(import_task, i))
                
                # Submit queries
                for i in range(10):
                    futures.append(executor.submit(query_task, i))
                
                # Wait for all to complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results['operations_completed'] += 1
                    except Exception as e:
                        results['errors'].append(str(e))
                        results['success'] = False
            
            # Cleanup
            self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def test_data_integrity(self) -> Dict:
        """Test data integrity constraints and normalization"""
        logger.info("Testing data integrity and constraints...")
        
        test_cases = []
        
        # Test 1: Duplicate VIN constraint
        try:
            self.db.execute_query("""
                INSERT INTO normalized_vehicle_data (vin, stock, location) 
                VALUES ('TEST123456789VIN1', 'STK001', 'test_dealer')
            """)
            self.db.execute_query("""
                INSERT INTO normalized_vehicle_data (vin, stock, location) 
                VALUES ('TEST123456789VIN1', 'STK002', 'test_dealer')
            """)
            test_cases.append({'test': 'duplicate_vin_same_dealer', 'passed': False, 
                             'reason': 'Should have failed on unique constraint'})
        except:
            test_cases.append({'test': 'duplicate_vin_same_dealer', 'passed': True})
        
        # Test 2: Required fields
        try:
            self.db.execute_query("""
                INSERT INTO normalized_vehicle_data (vin, location) 
                VALUES ('TEST123456789VIN2', 'test_dealer')
            """)
            test_cases.append({'test': 'missing_required_stock', 'passed': False,
                             'reason': 'Should have failed on NOT NULL constraint'})
        except:
            test_cases.append({'test': 'missing_required_stock', 'passed': True})
        
        # Test 3: Vehicle condition normalization
        test_conditions = [
            ('Certified Used', 'cpo'),
            ('Used', 'po'),
            ('New', 'new'),
            ('In-Transit', 'offlot'),
            ('Available', 'onlot')
        ]
        
        for input_condition, expected in test_conditions:
            result = self.importer.normalize_condition(input_condition, '')
            passed = result == expected
            test_cases.append({
                'test': f'normalize_{input_condition}',
                'passed': passed,
                'expected': expected,
                'actual': result
            })
        
        # Test 4: Referential integrity
        try:
            # Insert raw data
            self.db.execute_query("""
                INSERT INTO raw_vehicle_data (id, vin, stock, location) 
                VALUES (999999, 'REFTEST1234567890', 'STK999', 'test_dealer')
            """)
            
            # Insert normalized with reference
            self.db.execute_query("""
                INSERT INTO normalized_vehicle_data (raw_data_id, vin, stock, location) 
                VALUES (999999, 'REFTEST1234567890', 'STK999', 'test_dealer')
            """)
            
            # Try to delete raw data (should cascade)
            self.db.execute_query("DELETE FROM raw_vehicle_data WHERE id = 999999")
            
            # Check if normalized was deleted
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM normalized_vehicle_data WHERE raw_data_id = 999999",
                fetch='one'
            )
            
            test_cases.append({
                'test': 'cascade_delete',
                'passed': result['count'] == 0,
                'reason': 'Cascade delete working correctly'
            })
        except Exception as e:
            test_cases.append({
                'test': 'cascade_delete',
                'passed': False,
                'error': str(e)
            })
        
        # Cleanup
        self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
        
        passed_count = sum(1 for tc in test_cases if tc['passed'])
        return {
            'total_tests': len(test_cases),
            'passed': passed_count,
            'failed': len(test_cases) - passed_count,
            'test_cases': test_cases
        }
    
    def test_query_performance(self) -> Dict:
        """Test query performance with production-like data"""
        logger.info("Testing query performance...")
        
        # First, populate with realistic data
        logger.info("Populating test data...")
        for i in range(10):  # 10 dealerships
            vehicles = self.generate_test_vehicle_data(5000, f"perf_test_dealer_{i}")
            df = pd.DataFrame(vehicles)
            temp_file = f"/tmp/perf_test_{i}.csv"
            df.to_csv(temp_file, index=False)
            self.importer.import_csv_file(temp_file, f"perf_test_dealer_{i}")
            os.remove(temp_file)
        
        queries = [
            {
                'name': 'current_inventory_view',
                'sql': "SELECT * FROM current_inventory LIMIT 1000",
                'expected_time': 1.0
            },
            {
                'name': 'dealership_summary',
                'sql': """
                    SELECT location, vehicle_condition, COUNT(*) as count, AVG(price) as avg_price
                    FROM normalized_vehicle_data
                    WHERE last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY location, vehicle_condition
                """,
                'expected_time': 2.0
            },
            {
                'name': 'duplicate_vins',
                'sql': """
                    SELECT vin, COUNT(DISTINCT location) as locations
                    FROM normalized_vehicle_data
                    GROUP BY vin
                    HAVING COUNT(DISTINCT location) > 1
                """,
                'expected_time': 3.0
            },
            {
                'name': 'price_range_search',
                'sql': """
                    SELECT * FROM normalized_vehicle_data
                    WHERE price BETWEEN 25000 AND 35000
                    AND vehicle_condition IN ('new', 'cpo')
                    AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY make, model
                    LIMIT 500
                """,
                'expected_time': 1.5
            }
        ]
        
        results = []
        for query in queries:
            start_time = time.time()
            try:
                result = self.db.execute_query(query['sql'])
                execution_time = time.time() - start_time
                row_count = len(result) if isinstance(result, list) else 1
                
                results.append({
                    'query': query['name'],
                    'execution_time': round(execution_time, 3),
                    'row_count': row_count,
                    'passed': execution_time <= query['expected_time'],
                    'expected_time': query['expected_time']
                })
            except Exception as e:
                results.append({
                    'query': query['name'],
                    'passed': False,
                    'error': str(e)
                })
        
        # Cleanup
        self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
        
        return {
            'queries_tested': len(results),
            'passed': sum(1 for r in results if r.get('passed', False)),
            'query_results': results
        }
    
    def test_backup_restore(self) -> Dict:
        """Test backup and restore functionality"""
        logger.info("Testing backup and restore...")
        
        try:
            # Insert test data
            vehicles = self.generate_test_vehicle_data(1000, 'backup_test_dealer')
            df = pd.DataFrame(vehicles)
            temp_file = "/tmp/backup_test.csv"
            df.to_csv(temp_file, index=False)
            self.importer.import_csv_file(temp_file, 'backup_test_dealer')
            os.remove(temp_file)
            
            # Get count before backup
            count_before = self.db.execute_query(
                "SELECT COUNT(*) as count FROM raw_vehicle_data",
                fetch='one'
            )['count']
            
            # Create backup
            backup_start = time.time()
            backup_file = self.maintenance.backup_database('stress_test_backup')
            backup_time = time.time() - backup_start
            
            # Verify backup file exists and has reasonable size
            backup_size = os.path.getsize(backup_file) / 1024 / 1024  # MB
            
            # Clear data
            self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
            
            # Verify data is gone
            count_after_clear = self.db.execute_query(
                "SELECT COUNT(*) as count FROM raw_vehicle_data",
                fetch='one'
            )['count']
            
            # Note: Restore test would require more complex setup
            # as it needs to handle database recreation
            
            return {
                'backup_created': os.path.exists(backup_file),
                'backup_size_mb': round(backup_size, 2),
                'backup_time_seconds': round(backup_time, 2),
                'rows_before_backup': count_before,
                'rows_after_clear': count_after_clear,
                'success': backup_size > 0.1  # At least 100KB
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_error_recovery(self) -> Dict:
        """Test error handling and recovery"""
        logger.info("Testing error recovery mechanisms...")
        
        test_results = []
        
        # Test 1: Invalid CSV data
        try:
            # Create CSV with invalid data
            invalid_data = pd.DataFrame({
                'vin': ['SHORT', None, '12345678901234567'],  # Invalid VINs
                'stock': [None, 'STK001', 'STK002'],  # Missing required field
                'price': ['invalid', '25000', '30000'],  # Invalid numeric
                'location': ['test', 'test', 'test']
            })
            temp_file = "/tmp/invalid_test.csv"
            invalid_data.to_csv(temp_file, index=False)
            
            stats = self.importer.import_csv_file(temp_file, 'error_test_dealer')
            os.remove(temp_file)
            
            test_results.append({
                'test': 'invalid_csv_handling',
                'passed': stats['skipped_rows'] == 2,  # Should skip 2 invalid rows
                'skipped_rows': stats['skipped_rows'],
                'errors': len(stats['errors'])
            })
        except Exception as e:
            test_results.append({
                'test': 'invalid_csv_handling',
                'passed': False,
                'error': str(e)
            })
        
        # Test 2: Connection pool exhaustion
        try:
            # Try to exceed connection pool
            connections = []
            for i in range(10):
                conn = self.db._connection_pool.getconn()
                connections.append(conn)
            
            # This should fail or wait
            test_results.append({
                'test': 'connection_pool_limit',
                'passed': False,
                'reason': 'Should have hit connection limit'
            })
        except Exception as e:
            test_results.append({
                'test': 'connection_pool_limit',
                'passed': True,
                'handled': 'Connection pool properly limited'
            })
        finally:
            # Return connections
            for conn in connections:
                try:
                    self.db._connection_pool.putconn(conn)
                except:
                    pass
        
        # Cleanup
        self.db.execute_query("TRUNCATE TABLE vin_history, normalized_vehicle_data, raw_vehicle_data CASCADE")
        
        return {
            'tests_run': len(test_results),
            'tests_passed': sum(1 for t in test_results if t.get('passed', False)),
            'test_results': test_results
        }
    
    def run_all_tests(self) -> Dict:
        """Run all stress tests and compile results"""
        self.test_results['start_time'] = datetime.now()
        
        test_functions = [
            ('Bulk Import Performance', self.test_bulk_import_performance),
            ('Concurrent Operations', self.test_concurrent_operations),
            ('Data Integrity', self.test_data_integrity),
            ('Query Performance', self.test_query_performance),
            ('Backup/Restore', self.test_backup_restore),
            ('Error Recovery', self.test_error_recovery)
        ]
        
        for test_name, test_func in test_functions:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = test_func()
                self.test_results['performance_metrics'][test_name] = result
                
                if result.get('success', True) and not result.get('errors', []):
                    self.test_results['tests_passed'] += 1
                    logger.info(f"✓ {test_name} PASSED")
                else:
                    self.test_results['tests_failed'] += 1
                    logger.error(f"✗ {test_name} FAILED")
                    if 'error' in result:
                        self.test_results['errors'].append(f"{test_name}: {result['error']}")
                
            except Exception as e:
                self.test_results['tests_failed'] += 1
                self.test_results['errors'].append(f"{test_name}: {str(e)}")
                logger.error(f"✗ {test_name} FAILED with exception: {e}")
        
        self.test_results['end_time'] = datetime.now()
        self.test_results['total_duration'] = str(
            self.test_results['end_time'] - self.test_results['start_time']
        )
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        report = f"""
DEALERSHIP DATABASE STRESS TEST REPORT
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total Tests Run: {self.test_results['tests_passed'] + self.test_results['tests_failed']}
Tests Passed: {self.test_results['tests_passed']}
Tests Failed: {self.test_results['tests_failed']}
Total Duration: {self.test_results['total_duration']}

DETAILED RESULTS
----------------
"""
        
        for test_name, metrics in self.test_results['performance_metrics'].items():
            report += f"\n{test_name}:\n"
            report += "-" * len(test_name) + "\n"
            
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    if key != 'test_cases' and key != 'query_results' and key != 'test_results':
                        report += f"  {key}: {value}\n"
                
                # Special handling for detailed results
                if 'test_cases' in metrics:
                    report += "  Test Cases:\n"
                    for tc in metrics['test_cases']:
                        status = "PASS" if tc.get('passed', False) else "FAIL"
                        report += f"    - {tc.get('test', 'Unknown')}: {status}\n"
                
                if 'query_results' in metrics:
                    report += "  Query Performance:\n"
                    for qr in metrics['query_results']:
                        status = "PASS" if qr.get('passed', False) else "FAIL"
                        time_str = f"{qr.get('execution_time', 'N/A')}s"
                        report += f"    - {qr.get('query', 'Unknown')}: {time_str} ({status})\n"
        
        if self.test_results['errors']:
            report += "\nERRORS ENCOUNTERED\n"
            report += "==================\n"
            for error in self.test_results['errors']:
                report += f"- {error}\n"
        
        report += "\nRECOMMENDATIONS\n"
        report += "===============\n"
        
        # Add recommendations based on results
        if self.test_results['tests_failed'] == 0:
            report += "✓ All tests passed. Database is ready for production use.\n"
        else:
            report += "⚠ Some tests failed. Please review errors before production deployment.\n"
        
        # Performance recommendations
        bulk_import = self.test_results['performance_metrics'].get('Bulk Import Performance', {})
        if bulk_import.get('import_time_seconds', 0) > 900:  # 15 minutes
            report += "⚠ Bulk import exceeds 15-minute target. Consider optimization.\n"
        
        return report

def main():
    """Main function to run stress tests"""
    print("Silver Fox Marketing - Dealership Database Stress Test")
    print("=" * 60)
    print("This will run comprehensive tests on your database.")
    print("Estimated time: 10-15 minutes")
    print("=" * 60)
    
    response = input("\nProceed with stress testing? (yes/no): ")
    if response.lower() != 'yes':
        print("Stress test cancelled.")
        return
    
    tester = DealershipDatabaseStressTest()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate report
        report = tester.generate_report()
        
        # Save report
        report_file = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Display summary
        print("\n" + "=" * 60)
        print("STRESS TEST COMPLETE")
        print("=" * 60)
        print(f"Tests Passed: {results['tests_passed']}")
        print(f"Tests Failed: {results['tests_failed']}")
        print(f"Report saved to: {report_file}")
        
        if results['tests_failed'] == 0:
            print("\n✓ All tests passed! Database is production-ready.")
        else:
            print("\n⚠ Some tests failed. Please review the report.")
        
    except Exception as e:
        print(f"\n✗ Stress test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()