"""
Error recovery and resilience mechanisms for Silver Fox Marketing dealership database
Handles various failure scenarios and provides automatic recovery capabilities
"""
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import psycopg2
from psycopg2 import OperationalError, InterfaceError
import json
from database_connection import db_manager, DatabaseConnectionError
from database_config import config
from csv_importer import CSVImporter
from database_maintenance import DatabaseMaintenance

logger = logging.getLogger(__name__)

class DatabaseRecoveryManager:
    """Handles database recovery and resilience operations"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.importer = CSVImporter()
        self.maintenance = DatabaseMaintenance()
        self.recovery_log = []
    
    def log_recovery_action(self, action: str, details: Dict = None, success: bool = True):
        """Log recovery actions for audit trail"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {},
            'success': success
        }
        self.recovery_log.append(entry)
        
        if success:
            logger.info(f"Recovery action successful: {action}")
        else:
            logger.error(f"Recovery action failed: {action}")
    
    def test_database_connectivity(self, max_retries: int = 3) -> bool:
        """Test database connectivity with retry logic"""
        for attempt in range(max_retries):
            try:
                result = self.db.execute_query("SELECT 1", fetch='one')
                if result:
                    self.log_recovery_action("database_connectivity_test", 
                                           {"attempt": attempt + 1}, True)
                    return True
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"Connectivity test attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        
        self.log_recovery_action("database_connectivity_test", 
                               {"max_attempts": max_retries}, False)
        return False
    
    def recover_connection_pool(self) -> bool:
        """Recover connection pool after failures"""
        try:
            logger.info("Attempting connection pool recovery...")
            
            # Close existing pool
            if hasattr(self.db, '_connection_pool') and self.db._connection_pool:
                self.db._connection_pool.closeall()
            
            # Reinitialize pool
            self.db._initialize_pool()
            
            # Test connectivity
            if self.test_database_connectivity():
                self.log_recovery_action("connection_pool_recovery", success=True)
                return True
            else:
                self.log_recovery_action("connection_pool_recovery", success=False)
                return False
                
        except Exception as e:
            self.log_recovery_action("connection_pool_recovery", 
                                   {"error": str(e)}, False)
            return False
    
    def recover_corrupted_import(self, csv_file: str, dealership_name: str) -> Dict:
        """Recover from corrupted CSV import"""
        recovery_result = {
            'original_file': csv_file,
            'dealership': dealership_name,
            'recovery_successful': False,
            'actions_taken': [],
            'final_stats': {}
        }
        
        try:
            logger.info(f"Attempting recovery for corrupted import: {csv_file}")
            
            # Step 1: Backup original file
            backup_path = f"{csv_file}.backup_{int(time.time())}"
            os.rename(csv_file, backup_path)
            recovery_result['actions_taken'].append(f"Backed up to {backup_path}")
            
            # Step 2: Try to clean the CSV file
            cleaned_file = self.clean_corrupted_csv(backup_path, csv_file)
            if cleaned_file:
                recovery_result['actions_taken'].append("CSV file cleaned")
                
                # Step 3: Attempt import with cleaned file
                import_stats = self.importer.import_csv_file(csv_file, dealership_name)
                recovery_result['final_stats'] = import_stats
                
                if import_stats['imported_rows'] > 0:
                    recovery_result['recovery_successful'] = True
                    recovery_result['actions_taken'].append("Import successful with cleaned data")
                else:
                    recovery_result['actions_taken'].append("Import failed even with cleaned data")
            
            self.log_recovery_action("corrupted_import_recovery", recovery_result)
            
        except Exception as e:
            recovery_result['actions_taken'].append(f"Recovery failed: {str(e)}")
            self.log_recovery_action("corrupted_import_recovery", recovery_result, False)
        
        return recovery_result
    
    def clean_corrupted_csv(self, source_file: str, output_file: str) -> bool:
        """Attempt to clean corrupted CSV data"""
        try:
            import pandas as pd
            import csv
            
            logger.info(f"Cleaning corrupted CSV: {source_file}")
            
            # Try different encodings and error handling
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    # Read with error handling
                    df = pd.read_csv(source_file, encoding=encoding, 
                                   on_bad_lines='skip', dtype=str)
                    
                    # Basic cleaning
                    # Remove completely empty rows
                    df = df.dropna(how='all')
                    
                    # Remove rows with all empty strings
                    df = df.replace('', pd.NA).dropna(how='all').fillna('')
                    
                    # Ensure required columns exist
                    required_cols = ['vin', 'stock']
                    for col in required_cols:
                        if col not in df.columns:
                            df[col] = ''
                    
                    # Remove obvious bad data
                    # Remove rows where VIN is not 17 characters
                    df = df[df['vin'].str.len() == 17]
                    
                    # Remove rows with missing stock numbers
                    df = df[df['stock'].str.strip() != '']
                    
                    # Save cleaned file
                    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL)
                    
                    logger.info(f"CSV cleaned successfully using {encoding} encoding")
                    return True
                    
                except UnicodeDecodeError:
                    continue  # Try next encoding
                except Exception as e:
                    logger.warning(f"Failed to clean with {encoding}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"CSV cleaning failed: {e}")
            return False
    
    def recover_missing_dealership_data(self, dealership_name: str, 
                                      days_missing: int = 1) -> Dict:
        """Attempt to recover missing dealership data"""
        recovery_result = {
            'dealership': dealership_name,
            'days_missing': days_missing,
            'recovery_attempts': [],
            'data_recovered': False
        }
        
        try:
            logger.info(f"Attempting data recovery for {dealership_name}")
            
            # Check if there are backup CSV files
            import_path = config.import_path
            backup_files = []
            
            # Look for recent backup files
            for i in range(days_missing):
                check_date = datetime.now() - timedelta(days=i+1)
                date_str = check_date.strftime('%Y%m%d')
                
                possible_files = [
                    f"{dealership_name}_{date_str}.csv",
                    f"{dealership_name}.csv.backup_{date_str}",
                    f"{dealership_name}_backup.csv"
                ]
                
                for filename in possible_files:
                    filepath = os.path.join(import_path, filename)
                    if os.path.exists(filepath):
                        backup_files.append(filepath)
            
            # Attempt to import backup files
            for backup_file in backup_files:
                try:
                    stats = self.importer.import_csv_file(backup_file, dealership_name)
                    recovery_result['recovery_attempts'].append({
                        'file': backup_file,
                        'success': True,
                        'rows_imported': stats['imported_rows']
                    })
                    
                    if stats['imported_rows'] > 0:
                        recovery_result['data_recovered'] = True
                        break
                        
                except Exception as e:
                    recovery_result['recovery_attempts'].append({
                        'file': backup_file,
                        'success': False,
                        'error': str(e)
                    })
            
            self.log_recovery_action("missing_dealership_data_recovery", recovery_result)
            
        except Exception as e:
            recovery_result['recovery_attempts'].append({
                'error': f"Recovery process failed: {str(e)}"
            })
            self.log_recovery_action("missing_dealership_data_recovery", 
                                   recovery_result, False)
        
        return recovery_result
    
    def recover_database_corruption(self) -> Dict:
        """Attempt to recover from database corruption"""
        recovery_result = {
            'corruption_detected': False,
            'recovery_actions': [],
            'recovery_successful': False
        }
        
        try:
            logger.info("Checking for database corruption...")
            
            # Check for corruption indicators
            corruption_checks = [
                self.check_table_corruption(),
                self.check_index_corruption(),
                self.check_data_integrity()
            ]
            
            corruption_found = any(corruption_checks)
            recovery_result['corruption_detected'] = corruption_found
            
            if corruption_found:
                logger.warning("Database corruption detected, attempting recovery...")
                
                # Step 1: Create emergency backup
                try:
                    backup_file = self.maintenance.backup_database('emergency_before_recovery')
                    recovery_result['recovery_actions'].append(f"Emergency backup created: {backup_file}")
                except Exception as e:
                    recovery_result['recovery_actions'].append(f"Emergency backup failed: {str(e)}")
                
                # Step 2: Run database repair operations
                repair_success = self.repair_database_corruption()
                recovery_result['recovery_actions'].append(f"Database repair: {'success' if repair_success else 'failed'}")
                
                # Step 3: Verify repair
                post_repair_checks = [
                    self.check_table_corruption(),
                    self.check_index_corruption(),
                    self.check_data_integrity()
                ]
                
                recovery_result['recovery_successful'] = not any(post_repair_checks)
                
                if recovery_result['recovery_successful']:
                    recovery_result['recovery_actions'].append("Corruption successfully repaired")
                else:
                    recovery_result['recovery_actions'].append("Corruption repair incomplete")
            
            self.log_recovery_action("database_corruption_recovery", recovery_result)
            
        except Exception as e:
            recovery_result['recovery_actions'].append(f"Recovery process failed: {str(e)}")
            self.log_recovery_action("database_corruption_recovery", 
                                   recovery_result, False)
        
        return recovery_result
    
    def check_table_corruption(self) -> bool:
        """Check for table-level corruption"""
        try:
            # Simple corruption check - try to count rows in each table
            tables = ['raw_vehicle_data', 'normalized_vehicle_data', 'vin_history', 'dealership_configs']
            
            for table in tables:
                result = self.db.execute_query(f"SELECT COUNT(*) FROM {table}", fetch='one')
                if result is None:
                    return True  # Corruption detected
            
            return False  # No corruption
            
        except Exception as e:
            logger.error(f"Table corruption check failed: {e}")
            return True  # Assume corruption if check fails
    
    def check_index_corruption(self) -> bool:
        """Check for index corruption"""
        try:
            # Check if indexes are being used properly
            result = self.db.execute_query("""
                SELECT schemaname, tablename, indexname, idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0 AND schemaname = 'public'
            """)
            
            # If all indexes have zero scans, might indicate corruption
            if len(result) > 10:  # Arbitrary threshold
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Index corruption check failed: {e}")
            return True
    
    def check_data_integrity(self) -> bool:
        """Check for data integrity issues"""
        try:
            # Check for orphaned records
            orphaned_check = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM normalized_vehicle_data n
                LEFT JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                WHERE n.raw_data_id IS NOT NULL AND r.id IS NULL
            """, fetch='one')
            
            if orphaned_check['count'] > 100:  # Too many orphaned records
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            return True
    
    def repair_database_corruption(self) -> bool:
        """Attempt to repair database corruption"""
        try:
            logger.info("Attempting database corruption repair...")
            
            # Reindex all tables
            with self.db.get_connection() as conn:
                conn.set_isolation_level(0)  # AUTOCOMMIT mode
                with conn.cursor() as cursor:
                    cursor.execute("REINDEX DATABASE dealership_db")
            
            # Vacuum all tables
            self.db.vacuum_analyze()
            
            # Clean up orphaned records
            self.db.execute_query("""
                DELETE FROM normalized_vehicle_data
                WHERE raw_data_id IS NOT NULL
                AND raw_data_id NOT IN (SELECT id FROM raw_vehicle_data)
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False
    
    def create_recovery_report(self) -> str:
        """Generate a recovery report"""
        if not self.recovery_log:
            return "No recovery actions recorded."
        
        report = f"""
SILVER FOX MARKETING - DATABASE RECOVERY REPORT
==============================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RECOVERY ACTIONS SUMMARY
========================
Total Actions: {len(self.recovery_log)}
Successful: {sum(1 for entry in self.recovery_log if entry['success'])}
Failed: {sum(1 for entry in self.recovery_log if not entry['success'])}

DETAILED RECOVERY LOG
=====================
"""
        
        for entry in self.recovery_log:
            status = "✓" if entry['success'] else "✗"
            report += f"{status} {entry['timestamp']} - {entry['action']}\n"
            
            if entry['details']:
                for key, value in entry['details'].items():
                    report += f"    {key}: {value}\n"
            
            report += "\n"
        
        return report
    
    def run_recovery_health_check(self) -> Dict:
        """Run comprehensive recovery health check"""
        health_check = {
            'timestamp': datetime.now(),
            'database_connectivity': False,
            'connection_pool_health': False,
            'data_integrity': False,
            'recent_imports_status': {},
            'recommendations': []
        }
        
        try:
            # Test database connectivity
            health_check['database_connectivity'] = self.test_database_connectivity()
            
            # Test connection pool
            if health_check['database_connectivity']:
                try:
                    pool = self.db._connection_pool
                    health_check['connection_pool_health'] = True
                except:
                    health_check['connection_pool_health'] = False
            
            # Check data integrity
            corruption_detected = any([
                self.check_table_corruption(),
                self.check_index_corruption(),
                self.check_data_integrity()
            ])
            health_check['data_integrity'] = not corruption_detected
            
            # Check recent imports
            try:
                recent_imports = self.db.execute_query("""
                    SELECT 
                        location,
                        MAX(import_date) as last_import,
                        COUNT(*) as total_records
                    FROM raw_vehicle_data
                    WHERE import_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY location
                    ORDER BY last_import DESC
                """)
                
                for import_record in recent_imports:
                    days_since_import = (datetime.now().date() - import_record['last_import']).days
                    health_check['recent_imports_status'][import_record['location']] = {
                        'last_import': import_record['last_import'].isoformat(),
                        'days_since_import': days_since_import,
                        'total_records': import_record['total_records'],
                        'status': 'healthy' if days_since_import <= 1 else 'stale'
                    }
            except Exception as e:
                health_check['recent_imports_status'] = {'error': str(e)}
            
            # Generate recommendations
            if not health_check['database_connectivity']:
                health_check['recommendations'].append("CRITICAL: Database connectivity failed - check PostgreSQL service")
            
            if not health_check['connection_pool_health']:
                health_check['recommendations'].append("HIGH: Connection pool issues detected - restart application")
            
            if not health_check['data_integrity']:
                health_check['recommendations'].append("HIGH: Data integrity issues detected - run corruption recovery")
            
            stale_dealers = [dealer for dealer, status in health_check['recent_imports_status'].items() 
                           if isinstance(status, dict) and status.get('status') == 'stale']
            
            if stale_dealers:
                health_check['recommendations'].append(f"MEDIUM: Stale data for dealerships: {', '.join(stale_dealers)}")
        
        except Exception as e:
            health_check['error'] = str(e)
            health_check['recommendations'].append(f"CRITICAL: Health check failed: {str(e)}")
        
        return health_check

def main():
    """Main function for recovery operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database recovery and resilience tools')
    parser.add_argument('--health-check', action='store_true', help='Run recovery health check')
    parser.add_argument('--test-connectivity', action='store_true', help='Test database connectivity')
    parser.add_argument('--recover-pool', action='store_true', help='Recover connection pool')
    parser.add_argument('--recover-import', help='Recover corrupted import (CSV file path)')
    parser.add_argument('--dealership', help='Dealership name for import recovery')
    parser.add_argument('--recover-missing', help='Recover missing data for dealership')
    parser.add_argument('--days', type=int, default=1, help='Days of missing data to recover')
    parser.add_argument('--recover-corruption', action='store_true', help='Recover from database corruption')
    parser.add_argument('--report', help='Generate recovery report file')
    
    args = parser.parse_args()
    
    recovery_manager = DatabaseRecoveryManager()
    
    try:
        if args.health_check:
            print("Running recovery health check...")
            results = recovery_manager.run_recovery_health_check()
            
            print(f"\nHealth Check Results:")
            print(f"Database Connectivity: {'✓' if results['database_connectivity'] else '✗'}")
            print(f"Connection Pool: {'✓' if results['connection_pool_health'] else '✗'}")
            print(f"Data Integrity: {'✓' if results['data_integrity'] else '✗'}")
            
            if results['recommendations']:
                print(f"\nRecommendations:")
                for rec in results['recommendations']:
                    print(f"  - {rec}")
        
        elif args.test_connectivity:
            print("Testing database connectivity...")
            success = recovery_manager.test_database_connectivity()
            print(f"Connectivity test: {'PASSED' if success else 'FAILED'}")
        
        elif args.recover_pool:
            print("Recovering connection pool...")
            success = recovery_manager.recover_connection_pool()
            print(f"Pool recovery: {'SUCCESSFUL' if success else 'FAILED'}")
        
        elif args.recover_import:
            if not args.dealership:
                print("Error: --dealership required for import recovery")
                return
            
            print(f"Recovering corrupted import: {args.recover_import}")
            result = recovery_manager.recover_corrupted_import(args.recover_import, args.dealership)
            print(f"Recovery: {'SUCCESSFUL' if result['recovery_successful'] else 'FAILED'}")
            
            for action in result['actions_taken']:
                print(f"  - {action}")
        
        elif args.recover_missing:
            print(f"Recovering missing data for {args.recover_missing}")
            result = recovery_manager.recover_missing_dealership_data(args.recover_missing, args.days)
            print(f"Data recovery: {'SUCCESSFUL' if result['data_recovered'] else 'FAILED'}")
        
        elif args.recover_corruption:
            print("Recovering from database corruption...")
            result = recovery_manager.recover_database_corruption()
            print(f"Corruption recovery: {'SUCCESSFUL' if result['recovery_successful'] else 'FAILED'}")
        
        else:
            parser.print_help()
        
        # Generate report if requested
        if args.report:
            report = recovery_manager.create_recovery_report()
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Recovery report saved to: {args.report}")
    
    except Exception as e:
        print(f"Recovery operation failed: {e}")
        raise

if __name__ == "__main__":
    main()