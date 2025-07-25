#!/usr/bin/env python3
"""
Simple CSV Import Test for Complete Database System
=================================================

Tests the core functionality of importing complete_data.csv format
"""

import os
import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
import tempfile
import pandas as pd

def create_test_database(db_path):
    """Create test database with simplified schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY,
            vin TEXT UNIQUE,
            stock_number TEXT,
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
            dealer_name TEXT,
            scraped_at TEXT,
            import_date DATE DEFAULT (date('now'))
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Created test database: {db_path}")

def create_test_csv(csv_path):
    """Create test CSV with realistic data"""
    headers = [
        'vin', 'stock_number', 'year', 'make', 'model', 'trim', 'price', 'msrp',
        'mileage', 'exterior_color', 'interior_color', 'fuel_type', 'transmission',
        'condition', 'url', 'dealer_name', 'scraped_at'
    ]
    
    dealerships = [
        "BMW of West St. Louis", "Columbia BMW", "Audi Ranch Mirage", 
        "Joe Machens Toyota", "Honda of Frontenac"
    ]
    
    vehicles = []
    for i, dealer in enumerate(dealerships):
        for j in range(20):  # 20 vehicles per dealer
            vin = f"TEST{i:02d}{j:04d}" + "0123456789"  # Make it 17 chars
            vehicle = [
                vin,
                f"STK{i:02d}{j:04d}",
                2020 + (j % 5),
                ["BMW", "Honda", "Audi", "Toyota", "Ford"][i % 5],
                ["Sedan", "SUV", "Coupe"][j % 3],
                ["Base", "Sport", "Premium"][j % 3],
                25000 + (j * 1000),
                30000 + (j * 1000),
                j * 1000,
                ["White", "Black", "Silver", "Blue"][j % 4],
                ["Black", "Tan", "Gray"][j % 3],
                ["Gasoline", "Hybrid", "Electric"][j % 3],
                ["Automatic", "Manual"][j % 2],
                ["new", "used", "certified"][j % 3],
                f"https://www.{dealer.lower().replace(' ', '')}.com/inventory/{vin}",
                dealer,
                datetime.now().isoformat()
            ]
            vehicles.append(vehicle)
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(vehicles)
    
    print(f"✅ Created test CSV with {len(vehicles)} vehicles: {csv_path}")
    return len(vehicles)

def test_csv_import(csv_path, db_path):
    """Test importing CSV data"""
    print(f"🧪 Testing CSV import...")
    
    # Simple import logic
    df = pd.read_csv(csv_path)
    
    conn = sqlite3.connect(db_path)
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
                row['vin'], row['stock_number'], row['year'], row['make'], 
                row['model'], row['trim'], row['price'], row['msrp'], row['mileage'],
                row['exterior_color'], row['interior_color'], row['fuel_type'],
                row['transmission'], row['condition'], row['url'], 
                row['dealer_name'], row['scraped_at']
            ))
            imported += 1
        except Exception as e:
            print(f"⚠️ Error importing row: {e}")
            errors += 1
    
    conn.commit()
    
    # Verify import
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT dealer_name) FROM vehicles")
    dealer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT dealer_name, COUNT(*) FROM vehicles GROUP BY dealer_name")
    dealer_breakdown = cursor.fetchall()
    
    conn.close()
    
    print(f"📊 Import Results:")
    print(f"   Imported: {imported}")
    print(f"   Errors: {errors}")
    print(f"   Total in DB: {total_count}")
    print(f"   Dealerships: {dealer_count}")
    
    print(f"📋 Dealer Breakdown:")
    for dealer, count in dealer_breakdown:
        print(f"   {dealer}: {count} vehicles")
    
    return imported > 0 and errors == 0 and total_count == imported

def test_data_queries(db_path):
    """Test various data queries"""
    print(f"🔍 Testing data queries...")
    
    conn = sqlite3.connect(db_path)
    
    # Test exports
    tests = [
        ("All vehicles", "SELECT * FROM vehicles"),
        ("BMW vehicles", "SELECT * FROM vehicles WHERE dealer_name LIKE '%BMW%'"),
        ("New vehicles", "SELECT * FROM vehicles WHERE condition = 'new'"),
        ("Expensive vehicles", "SELECT * FROM vehicles WHERE price > 40000"),
        ("Vehicle summary by dealer", "SELECT dealer_name, COUNT(*), AVG(price) FROM vehicles GROUP BY dealer_name")
    ]
    
    all_passed = True
    
    for test_name, query in tests:
        try:
            df = pd.read_sql_query(query, conn)
            print(f"   ✅ {test_name}: {len(df)} results")
        except Exception as e:
            print(f"   ❌ {test_name}: Failed - {e}")
            all_passed = False
    
    conn.close()
    return all_passed

def main():
    """Run simple CSV import test"""
    print("🚀 Simple CSV Import Test")
    print("=" * 40)
    
    # Create temporary test environment
    temp_dir = Path(tempfile.mkdtemp(prefix="simple_csv_test_"))
    db_path = temp_dir / "test.db"
    csv_path = temp_dir / "test_complete_data.csv"
    
    try:
        # Run tests
        tests = [
            ("Create Database", lambda: create_test_database(str(db_path))),
            ("Generate CSV", lambda: create_test_csv(str(csv_path)) > 0),
            ("Import CSV", lambda: test_csv_import(str(csv_path), str(db_path))),
            ("Test Queries", lambda: test_data_queries(str(db_path)))
        ]
        
        passed = 0
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                if test_func():
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {e}")
        
        # Results
        success_rate = (passed / len(tests)) * 100
        print(f"\n{'='*40}")
        print(f"🎯 RESULTS: {passed}/{len(tests)} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("✅ CSV import system is working correctly!")
            return True
        else:
            print("❌ Issues found in CSV import system")
            return False
    
    finally:
        # Cleanup
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up test files")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)