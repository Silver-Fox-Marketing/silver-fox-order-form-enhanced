"""
Database maintenance and backup scripts
Handles daily backups, cleanup, and optimization
"""
import os
import subprocess
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
import zipfile
import schedule
import time
from database_connection import db_manager
from database_config import config

logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    """Handles database maintenance tasks"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.pg_bin_path = r"C:\Program Files\PostgreSQL\16\bin"  # Adjust based on installation
    
    def backup_database(self, backup_name: str = None) -> str:
        """Create a database backup using pg_dump"""
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"dealership_db_backup_{timestamp}"
        
        backup_file = os.path.join(config.backup_path, f"{backup_name}.sql")
        
        # Build pg_dump command
        pg_dump = os.path.join(self.pg_bin_path, "pg_dump.exe")
        
        cmd = [
            pg_dump,
            f"--host={config.host}",
            f"--port={config.port}",
            f"--username={config.user}",
            f"--dbname={config.database}",
            "--format=plain",
            "--verbose",
            "--no-password",
            f"--file={backup_file}"
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = config.password
        
        try:
            logger.info(f"Starting database backup to {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Compress the backup
                zip_file = f"{backup_file}.zip"
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(backup_file, os.path.basename(backup_file))
                
                # Remove uncompressed file
                os.remove(backup_file)
                
                logger.info(f"Backup completed successfully: {zip_file}")
                return zip_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Backup error: {e}")
            raise
    
    def restore_database(self, backup_file: str):
        """Restore database from backup"""
        # Extract if compressed
        if backup_file.endswith('.zip'):
            with zipfile.ZipFile(backup_file, 'r') as zf:
                sql_file = zf.namelist()[0]
                zf.extractall(config.backup_path)
                backup_file = os.path.join(config.backup_path, sql_file)
        
        # Build psql command
        psql = os.path.join(self.pg_bin_path, "psql.exe")
        
        cmd = [
            psql,
            f"--host={config.host}",
            f"--port={config.port}",
            f"--username={config.user}",
            f"--dbname={config.database}",
            "--no-password",
            f"--file={backup_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = config.password
        
        try:
            logger.info(f"Restoring database from {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
            else:
                logger.error(f"Restore failed: {result.stderr}")
                raise Exception(f"psql failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Restore error: {e}")
            raise
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove old data from raw_vehicle_data table"""
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        try:
            # Delete old raw data
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM raw_vehicle_data WHERE import_date < %s",
                    (cutoff_date,)
                )
                deleted_raw = cursor.rowcount
                
            # Update normalized data to remove references to deleted raw data
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE normalized_vehicle_data 
                    SET raw_data_id = NULL 
                    WHERE raw_data_id NOT IN (
                        SELECT id FROM raw_vehicle_data
                    )
                    """
                )
                updated_normalized = cursor.rowcount
            
            logger.info(f"Cleanup completed: {deleted_raw} raw records deleted, "
                       f"{updated_normalized} normalized records updated")
            
            # Run VACUUM to reclaim space
            self.db.vacuum_analyze()
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Remove old backup files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        backup_files = list(Path(config.backup_path).glob("*.zip"))
        removed_count = 0
        
        for backup_file in backup_files:
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                removed_count += 1
                logger.info(f"Removed old backup: {backup_file}")
        
        logger.info(f"Removed {removed_count} old backup files")
    
    def update_statistics(self):
        """Update database statistics for query optimization"""
        tables = ['raw_vehicle_data', 'normalized_vehicle_data', 'vin_history']
        
        for table in tables:
            try:
                with self.db.get_connection() as conn:
                    conn.set_isolation_level(0)  # AUTOCOMMIT
                    with conn.cursor() as cursor:
                        cursor.execute(f"ANALYZE {table}")
                logger.info(f"Updated statistics for {table}")
            except Exception as e:
                logger.error(f"Failed to analyze {table}: {e}")
    
    def check_database_health(self) -> Dict:
        """Check database health metrics"""
        health_report = {
            'database_size': None,
            'table_sizes': {},
            'index_bloat': {},
            'dead_tuples': {},
            'connection_count': None,
            'slow_queries': []
        }
        
        try:
            # Database size
            size_query = """
                SELECT pg_database_size(current_database()) as size,
                       pg_size_pretty(pg_database_size(current_database())) as size_pretty
            """
            result = self.db.execute_query(size_query, fetch='one')
            health_report['database_size'] = result['size_pretty']
            
            # Table sizes and stats
            table_query = """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    CASE WHEN n_live_tup > 0 
                         THEN round(100.0 * n_dead_tup / n_live_tup, 2) 
                         ELSE 0 
                    END as dead_percent
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            
            tables = self.db.execute_query(table_query)
            for table in tables:
                health_report['table_sizes'][table['tablename']] = {
                    'size': table['total_size'],
                    'live_rows': table['live_rows'],
                    'dead_rows': table['dead_rows'],
                    'dead_percent': table['dead_percent']
                }
            
            # Connection count
            conn_query = "SELECT count(*) FROM pg_stat_activity"
            result = self.db.execute_query(conn_query, fetch='one')
            health_report['connection_count'] = result['count']
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_report['error'] = str(e)
            return health_report
    
    def run_daily_maintenance(self):
        """Run all daily maintenance tasks"""
        logger.info("Starting daily maintenance routine")
        
        try:
            # 1. Create backup
            backup_file = self.backup_database()
            
            # 2. Cleanup old data
            self.cleanup_old_data(days_to_keep=90)
            
            # 3. Cleanup old backups
            self.cleanup_old_backups(days_to_keep=30)
            
            # 4. Update statistics
            self.update_statistics()
            
            # 5. Check health
            health = self.check_database_health()
            logger.info(f"Database health: {health['database_size']} total size")
            
            logger.info("Daily maintenance completed successfully")
            
        except Exception as e:
            logger.error(f"Daily maintenance failed: {e}")
            raise

def setup_scheduled_maintenance():
    """Setup scheduled maintenance tasks"""
    maintenance = DatabaseMaintenance()
    
    # Schedule daily maintenance at 2 AM
    schedule.every().day.at("02:00").do(maintenance.run_daily_maintenance)
    
    # Schedule hourly statistics update
    schedule.every().hour.do(maintenance.update_statistics)
    
    logger.info("Scheduled maintenance tasks configured")
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database maintenance utilities')
    parser.add_argument('--backup', action='store_true', help='Create database backup')
    parser.add_argument('--restore', help='Restore from backup file')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old data')
    parser.add_argument('--health', action='store_true', help='Check database health')
    parser.add_argument('--daily', action='store_true', help='Run daily maintenance')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled maintenance')
    
    args = parser.parse_args()
    
    maintenance = DatabaseMaintenance()
    
    try:
        if args.backup:
            backup = maintenance.backup_database()
            print(f"Backup created: {backup}")
        
        elif args.restore:
            maintenance.restore_database(args.restore)
            print("Database restored successfully")
        
        elif args.cleanup:
            maintenance.cleanup_old_data()
            print("Cleanup completed")
        
        elif args.health:
            health = maintenance.check_database_health()
            print("\nDatabase Health Report:")
            print(f"Database Size: {health['database_size']}")
            print("\nTable Statistics:")
            for table, stats in health['table_sizes'].items():
                print(f"  {table}: {stats['size']} "
                      f"({stats['live_rows']} rows, {stats['dead_percent']}% dead)")
        
        elif args.daily:
            maintenance.run_daily_maintenance()
            print("Daily maintenance completed")
        
        elif args.schedule:
            print("Starting scheduled maintenance daemon...")
            setup_scheduled_maintenance()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Maintenance failed: {e}")
        raise

if __name__ == "__main__":
    main()