#!/usr/bin/env python3
"""
Final Production Readiness Test
==============================

Comprehensive test to validate the complete CSV database system
is ready for production deployment on MinisForum PC.
"""

import sys
import os
import sqlite3
import tempfile
import shutil
import time
from pathlib import Path
import pandas as pd
from datetime import datetime

class ProductionReadinessTest:
    """Complete production readiness validation"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="production_test_"))
        self.db_path = self.temp_dir / "production_test.db"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'performance': {},
            'data_quality': {},
            'ready_for_production': False
        }
        
    def setup_production_database(self):
        """Create production-ready database schema"""
        print("🗄️ Setting up production database schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main vehicles table (simplified production version)
        cursor.execute("""
            CREATE TABLE vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin TEXT NOT NULL,
                stock_number TEXT NOT NULL,
                year INTEGER,
                make TEXT,
                model TEXT,
                trim TEXT,
                price REAL,
                msrp REAL,
                mileage INTEGER,
                exterior_color TEXT,
                interior_color TEXT,
                fuel_type TEXT,
                transmission TEXT,
                condition TEXT,
                url TEXT,
                dealer_name TEXT NOT NULL,
                scraped_at TEXT,
                import_date DATE DEFAULT (date('now')),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vin, dealer_name) ON CONFLICT REPLACE
            )
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX idx_vin ON vehicles(vin)")
        cursor.execute("CREATE INDEX idx_dealer ON vehicles(dealer_name)")  
        cursor.execute("CREATE INDEX idx_condition ON vehicles(condition)")
        cursor.execute("CREATE INDEX idx_make_model ON vehicles(make, model)")
        cursor.execute("CREATE INDEX idx_price ON vehicles(price)")
        cursor.execute("CREATE INDEX idx_import_date ON vehicles(import_date)")
        
        # Summary table for quick reports
        cursor.execute("""
            CREATE TABLE dealer_summary (
                dealer_name TEXT PRIMARY KEY,
                total_vehicles INTEGER DEFAULT 0,
                avg_price REAL DEFAULT 0,
                new_count INTEGER DEFAULT 0,
                used_count INTEGER DEFAULT 0,
                certified_count INTEGER DEFAULT 0,
                last_import_date DATE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Production database schema created")
        return True
    
    def test_csv_import_performance(self):
        """Test CSV import performance with real data"""
        print("⚡ Testing CSV import performance...")
        
        # Find real CSV
        scraper_output_dir = Path("/Users/barretttaylor/Desktop/Claude Code/projects/silverfox_scraper_system/output_data")
        complete_csv_files = list(scraper_output_dir.glob("*/complete_data.csv"))
        if not complete_csv_files:
            print("❌ No complete_data.csv found")
            return False
            
        latest_csv = max(complete_csv_files, key=lambda x: x.stat().st_mtime) 
        
        # Measure import performance
        start_time = time.time()
        
        # Import data
        df = pd.read_csv(latest_csv)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        imported = 0
        errors = 0
        
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO vehicles 
                    (vin, stock_number, year, make, model, trim, price, msrp, mileage,
                     exterior_color, interior_color, fuel_type, transmission, condition,
                     url, dealer_name, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['vin'], row['stock_number'],
                    int(row['year']) if pd.notna(row['year']) else None,
                    row['make'], row['model'], row['trim'],
                    float(row['price']) if pd.notna(row['price']) else None,
                    float(row['msrp']) if pd.notna(row['msrp']) else None, 
                    int(row['mileage']) if pd.notna(row['mileage']) else None,
                    row['exterior_color'], row['interior_color'],
                    row['fuel_type'], row['transmission'], row['condition'],
                    row['url'], row['dealer_name'], row['scraped_at']
                ))
                imported += 1
            except Exception as e:
                errors += 1
        
        conn.commit()
        
        # Update dealer summary
        cursor.execute("""
            INSERT OR REPLACE INTO dealer_summary 
            (dealer_name, total_vehicles, avg_price, new_count, used_count, certified_count, last_import_date)
            SELECT 
                dealer_name,
                COUNT(*) as total_vehicles,
                AVG(price) as avg_price,
                SUM(CASE WHEN condition = 'new' THEN 1 ELSE 0 END) as new_count,
                SUM(CASE WHEN condition = 'used' THEN 1 ELSE 0 END) as used_count,
                SUM(CASE WHEN condition = 'certified' THEN 1 ELSE 0 END) as certified_count,
                date('now') as last_import_date
            FROM vehicles
            GROUP BY dealer_name
        """)
        
        conn.commit()
        conn.close()
        
        end_time = time.time()
        import_duration = end_time - start_time
        
        # Performance metrics
        rows_per_second = imported / import_duration if import_duration > 0 else 0
        
        self.results['performance'] = {
            'import_time_seconds': import_duration,
            'rows_imported': imported,
            'errors': errors,
            'rows_per_second': rows_per_second,
            'csv_size': len(df)
        }
        
        # Performance benchmarks (for MinisForum PC)
        performance_ok = (
            import_duration < 60 and  # Under 1 minute
            rows_per_second > 10 and  # At least 10 rows/sec
            errors == 0               # No errors
        )
        
        print(f"   Import time: {import_duration:.2f} seconds")
        print(f"   Rows imported: {imported:,}")
        print(f"   Performance: {rows_per_second:.0f} rows/second")
        print(f"   Errors: {errors}")
        
        if performance_ok:
            print("✅ Performance test passed")
            self.results['tests_passed'] += 1
            return True
        else:
            print("❌ Performance test failed")
            self.results['tests_failed'] += 1
            return False
    
    def test_data_quality_and_integrity(self):
        """Test data quality and integrity"""
        print("🔍 Testing data quality and integrity...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Quality checks
        checks = []
        
        # 1. Record counts
        total_records = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles", conn).iloc[0]['count']
        checks.append(("Total records > 0", total_records > 0))
        
        # 2. Unique VIN+Dealer combinations
        unique_vin_dealer = pd.read_sql_query("""
            SELECT COUNT(*) as count FROM (
                SELECT vin, dealer_name, COUNT(*) as cnt 
                FROM vehicles 
                GROUP BY vin, dealer_name 
                HAVING cnt > 1
            )
        """, conn).iloc[0]['count']
        checks.append(("No duplicate VIN+Dealer", unique_vin_dealer == 0))
        
        # 3. Required fields populated
        null_vins = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles WHERE vin IS NULL OR vin = ''", conn).iloc[0]['count']
        checks.append(("All VINs populated", null_vins == 0))
        
        null_dealers = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles WHERE dealer_name IS NULL OR dealer_name = ''", conn).iloc[0]['count']
        checks.append(("All dealers populated", null_dealers == 0))
        
        # 4. Price ranges reasonable
        invalid_prices = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles WHERE price < 0 OR price > 500000", conn).iloc[0]['count']
        checks.append(("Prices in valid range", invalid_prices == 0))
        
        # 5. Years reasonable
        invalid_years = pd.read_sql_query("SELECT COUNT(*) as count FROM vehicles WHERE year < 1980 OR year > 2026", conn).iloc[0]['count']
        checks.append(("Years in valid range", invalid_years == 0))
        
        # 6. Dealership coverage
        dealer_count = pd.read_sql_query("SELECT COUNT(DISTINCT dealer_name) as count FROM vehicles", conn).iloc[0]['count']
        checks.append(("Multiple dealerships", dealer_count >= 10))
        
        # 7. Condition values valid
        invalid_conditions = pd.read_sql_query("""
            SELECT COUNT(*) as count FROM vehicles 
            WHERE condition NOT IN ('new', 'used', 'certified', '') OR condition IS NULL
        """, conn).iloc[0]['count']
        checks.append(("Valid conditions", invalid_conditions == 0))
        
        conn.close()
        
        # Evaluate results
        passed_checks = sum(1 for _, result in checks if result)
        total_checks = len(checks)
        
        self.results['data_quality'] = {
            'total_records': int(total_records),
            'checks_passed': passed_checks,
            'total_checks': total_checks,
            'duplicate_vin_dealer': int(unique_vin_dealer),
            'dealer_count': int(dealer_count)
        }
        
        print(f"   Data quality checks: {passed_checks}/{total_checks} passed")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
        
        if passed_checks == total_checks:
            print("✅ Data quality test passed")
            self.results['tests_passed'] += 1
            return True
        else:
            print("❌ Data quality test failed")
            self.results['tests_failed'] += 1
            return False
    
    def test_query_performance(self):
        """Test query performance for common operations"""
        print("📊 Testing query performance...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Common queries with performance benchmarks
        queries = [
            ("All vehicles", "SELECT * FROM vehicles", 2.0),
            ("BMW vehicles", "SELECT * FROM vehicles WHERE dealer_name LIKE '%BMW%'", 1.0),
            ("New vehicles", "SELECT * FROM vehicles WHERE condition = 'new'", 1.0),
            ("Expensive vehicles", "SELECT * FROM vehicles WHERE price > 50000", 1.0),
            ("Dealer summary", "SELECT * FROM dealer_summary ORDER BY total_vehicles DESC", 0.5),
            ("VIN lookup", "SELECT * FROM vehicles WHERE vin = 'TEST123'", 0.1)
        ]
        
        all_passed = True
        
        for query_name, query, max_time in queries:
            start_time = time.time()
            try:
                df = pd.read_sql_query(query, conn)
                end_time = time.time()
                duration = end_time - start_time
                
                passed = duration <= max_time
                status = "✅" if passed else "❌"
                print(f"   {status} {query_name}: {duration:.3f}s ({len(df)} results)")
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {query_name}: Error - {e}")
                all_passed = False
        
        conn.close()
        
        if all_passed:
            print("✅ Query performance test passed")
            self.results['tests_passed'] += 1
            return True
        else:
            print("❌ Query performance test failed") 
            self.results['tests_failed'] += 1
            return False
    
    def test_export_functionality(self):
        """Test data export capabilities"""
        print("📤 Testing export functionality...")
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Export all vehicles
            all_vehicles = pd.read_sql_query("""
                SELECT vin, stock_number, year, make, model, trim, price, msrp,
                       condition, dealer_name, import_date
                FROM vehicles
                ORDER BY dealer_name, make, model
            """, conn)
            
            export_file = self.temp_dir / "all_vehicles_export.csv"
            all_vehicles.to_csv(export_file, index=False)
            
            # Export dealer summary
            dealer_summary = pd.read_sql_query("""
                SELECT dealer_name, total_vehicles, avg_price, new_count, used_count, certified_count
                FROM dealer_summary
                ORDER BY total_vehicles DESC
            """, conn)
            
            summary_file = self.temp_dir / "dealer_summary.csv"
            dealer_summary.to_csv(summary_file, index=False)
            
            # Export duplicate VINs report
            duplicates = pd.read_sql_query("""
                SELECT vin, COUNT(*) as dealer_count, 
                       GROUP_CONCAT(dealer_name) as dealerships
                FROM vehicles
                GROUP BY vin
                HAVING COUNT(*) > 1
                ORDER BY dealer_count DESC
            """, conn)
            
            duplicates_file = self.temp_dir / "duplicate_vins.csv"
            duplicates.to_csv(duplicates_file, index=False)
            
            conn.close()
            
            # Validate exports
            exports_valid = (
                export_file.exists() and export_file.stat().st_size > 0 and
                summary_file.exists() and summary_file.stat().st_size > 0 and
                duplicates_file.exists() and
                len(all_vehicles) > 0 and
                len(dealer_summary) > 0
            )
            
            print(f"   All vehicles export: {len(all_vehicles):,} records")
            print(f"   Dealer summary: {len(dealer_summary)} dealerships")
            print(f"   Duplicate VINs: {len(duplicates)} found")
            
            if exports_valid:
                print("✅ Export functionality test passed")
                self.results['tests_passed'] += 1
                return True
            else:
                print("❌ Export functionality test failed")
                self.results['tests_failed'] += 1
                return False
                
        except Exception as e:
            print(f"❌ Export test failed: {e}")
            self.results['tests_failed'] += 1
            return False
    
    def run_all_tests(self):
        """Run complete production readiness test suite"""
        print("🚀 PRODUCTION READINESS TEST")
        print("=" * 50)
        
        tests = [
            ("Database Setup", self.setup_production_database),
            ("CSV Import Performance", self.test_csv_import_performance),
            ("Data Quality & Integrity", self.test_data_quality_and_integrity), 
            ("Query Performance", self.test_query_performance),
            ("Export Functionality", self.test_export_functionality)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                print(f"💥 {test_name} failed with error: {e}")
                self.results['tests_failed'] += 1
        
        # Final assessment
        total_tests = len(tests)
        success_rate = (self.results['tests_passed'] / total_tests) * 100
        
        self.results['ready_for_production'] = success_rate >= 80
        
        print(f"\n{'='*50}")
        print(f"🏆 PRODUCTION READINESS RESULTS")
        print(f"{'='*50}")
        print(f"Tests Passed: {self.results['tests_passed']}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results['ready_for_production']:
            print("✅ SYSTEM IS PRODUCTION READY!")
            print("   Ready for deployment on MinisForum PC")
        else:
            print("❌ SYSTEM NEEDS WORK BEFORE PRODUCTION")
            print("   Review failed tests and fix issues")
        
        # Performance summary
        if 'performance' in self.results:
            perf = self.results['performance']
            print(f"\n⚡ PERFORMANCE SUMMARY:")
            print(f"   Import Speed: {perf['rows_per_second']:.0f} rows/second")
            print(f"   Import Time: {perf['import_time_seconds']:.1f} seconds")
            print(f"   Records Processed: {perf['rows_imported']:,}")
        
        # Data quality summary
        if 'data_quality' in self.results:
            dq = self.results['data_quality']
            print(f"\n🔍 DATA QUALITY SUMMARY:")
            print(f"   Total Records: {dq['total_records']:,}")
            print(f"   Dealerships: {dq['dealer_count']}")
            print(f"   Quality Checks: {dq['checks_passed']}/{dq['total_checks']} passed")
        
        return self.results
    
    def cleanup(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

def main():
    """Run production readiness test"""
    test_runner = ProductionReadinessTest()
    
    try:
        results = test_runner.run_all_tests()
        
        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        if results['ready_for_production']:
            print("✅ COMPLETE CSV DATABASE SYSTEM IS PRODUCTION READY!")
            print("✅ Safe to deploy on MinisForum PC")
            print("✅ All systems validated and tested")
            return 0
        else:
            print("❌ System needs additional work")
            print("❌ Do not deploy until issues are resolved")
            return 1
            
    finally:
        test_runner.cleanup()

if __name__ == "__main__":
    exit(main())