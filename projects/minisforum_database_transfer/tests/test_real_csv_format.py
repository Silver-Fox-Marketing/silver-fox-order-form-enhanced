#!/usr/bin/env python3
"""
Test with Real CSV Format from Silver Fox Scrapers
=================================================

Tests using actual complete_data.csv format from the scraper system
"""

import sys
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
import pandas as pd

def test_with_real_csv():
    """Test with real complete_data.csv file"""
    print("🧪 Testing with Real CSV Format")
    print("=" * 40)
    
    # Find the most recent complete_data.csv
    scraper_output_dir = Path("/Users/barretttaylor/Desktop/Claude Code/projects/silverfox_scraper_system/output_data")
    
    complete_csv_files = list(scraper_output_dir.glob("*/complete_data.csv"))
    if not complete_csv_files:
        print("❌ No complete_data.csv files found in scraper output")
        return False
    
    # Use the most recent one
    latest_csv = max(complete_csv_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 Using CSV: {latest_csv}")
    
    # Create temporary database
    temp_dir = Path(tempfile.mkdtemp(prefix="real_csv_test_"))
    db_path = temp_dir / "test.db"
    
    try:
        # Create database
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
        
        print(f"✅ Created test database")
        
        # Read and analyze CSV
        print(f"📊 Analyzing CSV file...")
        df = pd.read_csv(latest_csv)
        
        print(f"   Total rows: {len(df):,}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Dealerships: {df['dealer_name'].nunique()}")
        print(f"   Sample dealerships: {list(df['dealer_name'].unique()[:5])}")
        
        # Import data
        print(f"⚡ Importing data...")
        imported = 0
        errors = 0
        error_details = []
        
        for idx, row in df.iterrows():
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
                
                if imported % 500 == 0:
                    print(f"   📊 Imported {imported:,} vehicles...")
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only store first 5 errors
                    error_details.append(f"Row {idx+1}: {str(e)}")
        
        conn.commit()
        
        # Verify results
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        total_in_db = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT dealer_name) FROM vehicles")  
        unique_dealers = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT dealer_name, COUNT(*) as count 
            FROM vehicles 
            GROUP BY dealer_name 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_dealers = cursor.fetchall()
        
        # Test some queries
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE condition = 'new'")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE condition = 'used'")
        used_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE condition = 'certified'")
        certified_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(price) FROM vehicles WHERE price IS NOT NULL")
        avg_price = cursor.fetchone()[0]
        
        conn.close()
        
        # Results
        print(f"\n📊 IMPORT RESULTS:")
        print(f"   Successfully imported: {imported:,}")
        print(f"   Errors: {errors}")
        print(f"   Total in database: {total_in_db:,}")
        print(f"   Unique dealerships: {unique_dealers}")
        
        print(f"\n📋 TOP DEALERSHIPS:")
        for dealer, count in top_dealers:
            print(f"   {dealer}: {count} vehicles")
        
        print(f"\n🚗 VEHICLE CONDITIONS:")
        print(f"   New: {new_count:,}")
        print(f"   Used: {used_count:,}")  
        print(f"   Certified: {certified_count:,}")
        print(f"   Average Price: ${avg_price:,.2f}" if avg_price else "   Average Price: N/A")
        
        if error_details:
            print(f"\n⚠️ SAMPLE ERRORS:")
            for error in error_details:
                print(f"   {error}")
        
        # Success criteria
        success = (
            imported > 0 and
            total_in_db == imported and
            unique_dealers >= 5 and
            errors < len(df) * 0.1  # Less than 10% errors
        )
        
        print(f"\n{'='*40}")
        if success:
            print(f"✅ REAL CSV TEST PASSED!")
            print(f"   Import rate: {(imported/len(df)*100):.1f}%")
            print(f"   Ready for production use!")
        else:
            print(f"❌ REAL CSV TEST FAILED")
            print(f"   Check import logic and data quality")
        
        return success
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print(f"🧹 Test environment cleaned up")

if __name__ == "__main__":
    success = test_with_real_csv()
    exit(0 if success else 1)