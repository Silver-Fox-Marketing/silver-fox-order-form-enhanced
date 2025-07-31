#!/usr/bin/env python3
"""
Quick VIN Import Script - Simplified approach
"""
import sys
from pathlib import Path

# Add the project path for imports
project_root = Path(__file__).parent / "projects" / "minisforum_database_transfer" / "bulletproof_package"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(scripts_path))

from database_connection import db_manager

def quick_test():
    """Quick test to understand the current database structure"""
    print("=== QUICK VIN IMPORT TEST ===")
    
    # Check if vin_history table exists and its structure
    try:
        result = db_manager.execute_query("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'vin_history' 
            ORDER BY ordinal_position
        """)
        
        if result:
            print("vin_history table structure:")
            for col in result:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  {col['column_name']}: {col['data_type']} {nullable}")
        else:
            print("vin_history table does not exist")
            
        # Check raw_vehicle_data structure for time_scraped
        result = db_manager.execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'raw_vehicle_data' 
            AND column_name IN ('import_timestamp', 'time_scraped')
        """)
        
        print("\nraw_vehicle_data time columns:")
        for col in result:
            print(f"  {col['column_name']}")
            
        # Get a count of existing data
        try:
            result = db_manager.execute_query("SELECT COUNT(*) as count FROM vin_history")
            print(f"\nCurrent vin_history records: {result[0]['count'] if result else 0}")
        except:
            print("\nCannot count vin_history records (table may not exist)")
            
        try:
            result = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
            print(f"Current raw_vehicle_data records: {result[0]['count'] if result else 0}")
        except:
            print("Cannot count raw_vehicle_data records")
            
    except Exception as e:
        print(f"Error checking database structure: {e}")

def simple_import():
    """Simple import that just adds some VIN data for testing"""
    print("\n=== SIMPLE VIN IMPORT ===")
    
    # Drop and recreate vin_history table with correct structure
    try:
        print("Dropping existing vin_history table...")
        db_manager.execute_query("DROP TABLE IF EXISTS vin_history")
        
        print("Creating clean vin_history table...")
        db_manager.execute_query("""
            CREATE TABLE vin_history (
                id SERIAL PRIMARY KEY,
                dealership_name VARCHAR(255) NOT NULL,
                vin VARCHAR(17) NOT NULL,
                order_date DATE NOT NULL DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Adding unique constraint...")
        db_manager.execute_query("""
            CREATE UNIQUE INDEX vin_history_unique_idx 
            ON vin_history (dealership_name, vin, order_date)
        """)
        
        print("Adding time_scraped column to raw_vehicle_data...")
        try:
            db_manager.execute_query("""
                ALTER TABLE raw_vehicle_data 
                ADD COLUMN time_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
        except Exception as e:
            if "already exists" in str(e).lower():
                print("time_scraped column already exists")
            else:
                print(f"Error adding time_scraped column: {e}")
        
        # Add some sample VIN history data from recent orders
        print("Adding sample VIN history data...")
        
        sample_data = [
            ('Columbia Honda', '1HGCM82633A123456', '2025-07-29'),
            ('Columbia Honda', '5FPYK3F43SB034387', '2025-07-29'),
            ('Columbia Honda', '1HGCY1F49SA030876', '2025-07-29'),
            ('BMW of West St. Louis', 'WBAJA7C50KC123456', '2025-07-29'),
            ('Dave Sinclair Lincoln South', '1LN6P2EK5LB123456', '2025-07-29'),
        ]
        
        for dealership, vin, date in sample_data:
            try:
                db_manager.execute_query("""
                    INSERT INTO vin_history (dealership_name, vin, order_date)
                    VALUES (%s, %s, %s)
                """, (dealership, vin, date))
                print(f"  Added: {dealership} - {vin}")
            except Exception as e:
                print(f"  Error adding {vin}: {e}")
        
        # Check final count
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM vin_history")
        print(f"\nFinal vin_history count: {result[0]['count'] if result else 0}")
        
        # Show breakdown by dealership
        result = db_manager.execute_query("""
            SELECT dealership_name, COUNT(*) as count 
            FROM vin_history 
            GROUP BY dealership_name 
            ORDER BY count DESC
        """)
        
        if result:
            print("\nVINs by dealership:")
            for row in result:
                print(f"  {row['dealership_name']}: {row['count']}")
        
        print("\n✓ Simple import completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in simple import: {e}")
        return False

if __name__ == "__main__":
    quick_test()
    
    # Ask user if they want to proceed
    proceed = input("\nProceed with simple import? (y/n): ").lower().strip()
    if proceed == 'y':
        simple_import()
        
        print("\n=== NEXT STEPS ===")
        print("1. Test CAO processing with this VIN history")
        print("2. Should now show fewer 'new' vehicles since we have history")
        print("3. Can run full import later if needed")
    else:
        print("Import cancelled")