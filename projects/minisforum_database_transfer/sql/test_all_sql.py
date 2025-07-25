#!/usr/bin/env python3
"""
SQL Files Testing Script
=======================

Tests all SQL files to ensure they work correctly with PostgreSQL
before transferring to the MinisForum PC.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
import psycopg2
from psycopg2 import sql

class SQLTester:
    def __init__(self):
        self.sql_dir = Path(__file__).parent
        self.test_db_name = "test_minisforum_db"
        self.connection = None
        
    def create_test_database(self):
        """Create a temporary test database"""
        print("🗄️ Creating test database...")
        
        try:
            # Connect to postgres to create test database
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="your_password_here"  # Update this
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Drop if exists and create fresh
            cursor.execute(f"DROP DATABASE IF EXISTS {self.test_db_name}")
            cursor.execute(f"CREATE DATABASE {self.test_db_name}")
            
            cursor.close()
            conn.close()
            
            # Connect to new test database
            self.connection = psycopg2.connect(
                host="localhost",
                database=self.test_db_name,
                user="postgres",
                password="your_password_here"  # Update this
            )
            self.connection.autocommit = True
            
            print("✅ Test database created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test database: {e}")
            return False
    
    def test_sql_file(self, sql_file_path: Path) -> bool:
        """Test a single SQL file"""
        print(f"🧪 Testing {sql_file_path.name}...")
        
        try:
            cursor = self.connection.cursor()
            
            # Read and execute SQL file
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        print(f"   ✅ Statement {i+1}: OK")
                    except Exception as e:
                        print(f"   ❌ Statement {i+1}: {e}")
                        return False
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to test {sql_file_path.name}: {e}")
            return False
    
    def verify_tables_created(self) -> bool:
        """Verify all expected tables were created"""
        print("🔍 Verifying tables were created...")
        
        expected_tables = [
            'raw_vehicle_data',
            'normalized_vehicle_data', 
            'vin_history',
            'dealership_configs'
        ]
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            actual_tables = [row[0] for row in cursor.fetchall()]
            
            for table in expected_tables:
                if table in actual_tables:
                    print(f"   ✅ {table}: Found")
                else:
                    print(f"   ❌ {table}: Missing")
                    return False
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to verify tables: {e}")
            return False
    
    def verify_indexes_created(self) -> bool:
        """Verify all indexes were created"""
        print("🔍 Verifying indexes were created...")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            indexes = cursor.fetchall()
            
            if len(indexes) > 0:
                print(f"   ✅ Found {len(indexes)} indexes:")
                for index_name, table_name in indexes:
                    if not index_name.endswith('_pkey'):  # Skip primary key indexes
                        print(f"     - {table_name}.{index_name}")
                return True
            else:
                print("   ❌ No indexes found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to verify indexes: {e}")
            return False
    
    def verify_dealership_configs(self) -> bool:
        """Verify dealership configs were inserted correctly"""
        print("🔍 Verifying dealership configs...")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM dealership_configs")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT name FROM dealership_configs ORDER BY name LIMIT 10")
            sample_names = [row[0] for row in cursor.fetchall()]
            
            if count >= 30:  # Expect at least 30 dealerships
                print(f"   ✅ Found {count} dealership configurations")
                print(f"   📋 Sample dealerships: {', '.join(sample_names[:5])}...")
                return True
            else:
                print(f"   ❌ Only found {count} dealership configurations (expected 30+)")
                return False
                
        except Exception as e:
            print(f"❌ Failed to verify dealership configs: {e}")
            return False
    
    def cleanup(self):
        """Clean up test database"""
        print("🧹 Cleaning up test database...")
        
        try:
            if self.connection:
                self.connection.close()
            
            # Connect to postgres to drop test database
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="your_password_here"  # Update this
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {self.test_db_name}")
            cursor.close()
            conn.close()
            
            print("✅ Test database cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_all_tests(self) -> bool:
        """Run complete test suite"""
        print("🚀 SQL FILES TEST SUITE")
        print("=" * 50)
        
        try:
            # Create test database
            if not self.create_test_database():
                return False
            
            # Test SQL files in order
            sql_files = [
                self.sql_dir / "01_create_database.sql",
                self.sql_dir / "02_create_tables.sql", 
                self.sql_dir / "03_initial_dealership_configs.sql",
                self.sql_dir / "04_performance_settings.sql"
            ]
            
            for sql_file in sql_files:
                if sql_file.exists():
                    if not self.test_sql_file(sql_file):
                        return False
                else:
                    print(f"⚠️ Skipping {sql_file.name} (not found)")
            
            # Verification tests
            tests = [
                ("Table Creation", self.verify_tables_created),
                ("Index Creation", self.verify_indexes_created),
                ("Dealership Configs", self.verify_dealership_configs)
            ]
            
            for test_name, test_func in tests:
                print(f"\n🧪 Running: {test_name}")
                if not test_func():
                    return False
            
            print("\n" + "=" * 50)
            print("✅ ALL SQL TESTS PASSED!")
            print("✅ Files are ready for MinisForum transfer")
            return True
            
        except Exception as e:
            print(f"💥 Test suite failed: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """Run SQL file tests"""
    print("Note: Update the password in this script before running!")
    print("This script requires PostgreSQL to be running locally.")
    
    if input("Continue? (y/n): ").lower() != 'y':
        return 1
    
    tester = SQLTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())