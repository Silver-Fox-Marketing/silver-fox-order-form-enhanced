#!/usr/bin/env python3
"""
VIN History Import Script
Imports previous VIN logs to populate the vin_history table for accurate CAO processing
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the project path for imports
project_root = Path(__file__).parent / "projects" / "minisforum_database_transfer" / "bulletproof_package"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(scripts_path))

try:
    from database_connection import db_manager
    print("Database connection imported successfully")
except ImportError as e:
    print(f"Failed to import database connection: {e}")
    sys.exit(1)

class VINHistoryImporter:
    def __init__(self):
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def apply_schema_updates(self):
        """Apply database schema updates"""
        print("Applying database schema updates...")
        
        schema_updates = [
            # Create vin_history table if it doesn't exist
            """
            CREATE TABLE IF NOT EXISTS vin_history (
                id SERIAL PRIMARY KEY,
                dealership_name VARCHAR(255) NOT NULL,
                vin VARCHAR(17) NOT NULL,
                order_date DATE NOT NULL DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Add unique constraint separately
            """
            ALTER TABLE vin_history 
            ADD CONSTRAINT IF NOT EXISTS vin_history_unique 
            UNIQUE (dealership_name, vin, order_date);
            """,
            
            # Add time_scraped column to raw_vehicle_data
            """
            ALTER TABLE raw_vehicle_data 
            ADD COLUMN IF NOT EXISTS time_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            """,
            
            # Create indexes
            """
            CREATE INDEX IF NOT EXISTS idx_raw_vehicle_data_time_scraped 
            ON raw_vehicle_data(time_scraped);
            """,
            
            """
            CREATE INDEX IF NOT EXISTS idx_vin_history_dealership_date 
            ON vin_history(dealership_name, order_date);
            """,
            
            """
            CREATE INDEX IF NOT EXISTS idx_vin_history_vin 
            ON vin_history(vin);
            """,
            
            # Update existing records
            """
            UPDATE raw_vehicle_data 
            SET time_scraped = import_timestamp 
            WHERE time_scraped IS NULL AND import_timestamp IS NOT NULL;
            """,
            
            """
            UPDATE raw_vehicle_data 
            SET time_scraped = CURRENT_TIMESTAMP - INTERVAL '1 day'
            WHERE time_scraped IS NULL;
            """
        ]
        
        for i, update in enumerate(schema_updates, 1):
            try:
                db_manager.execute_query(update.strip())
                print(f"Schema update {i}/8 completed")
            except Exception as e:
                print(f"Schema update {i}/8 failed: {e}")
                
    def find_previous_orders(self):
        """Find all previous order files that contain VIN data"""
        order_paths = []
        
        # Search locations for previous orders
        search_paths = [
            Path("projects/minisforum_database_transfer/bulletproof_package/web_gui/orders"),
            Path("projects/minisforum_database_transfer/bulletproof_package/scripts/orders"),
            Path("projects/silverfox_scraper_system/silverfox_system/output_data"),
            Path("projects/shared_resources/Project reference for scraper/output_data")
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                print(f"Searching in: {search_path}")
                
                # Find CSV files
                csv_files = list(search_path.rglob("*.csv"))
                print(f"Found {len(csv_files)} CSV files")
                
                for csv_file in csv_files:
                    # Skip if it's clearly not a vehicle data file
                    if any(skip in str(csv_file).lower() for skip in ['test', 'backup', 'temp']):
                        continue
                        
                    order_paths.append(csv_file)
                    
                # Find JSON files (scraped data)
                json_files = list(search_path.rglob("*.json"))
                print(f"Found {len(json_files)} JSON files")
                
                for json_file in json_files:
                    if 'vehicles' in str(json_file).lower():
                        order_paths.append(json_file)
        
        print(f"Total files to process: {len(order_paths)}")
        return order_paths
        
    def extract_dealership_from_path(self, file_path):
        """Extract dealership name from file path"""
        path_str = str(file_path)
        
        # Common dealership name patterns
        dealership_patterns = [
            'Columbia_Honda', 'Columbia Honda',
            'BMW_of_West_St._Louis', 'BMW of West St. Louis',
            'Dave_Sinclair_Lincoln_South', 'Dave Sinclair Lincoln South',
            'Dave_Sinclair_Lincoln', 'Dave Sinclair Lincoln',
            'Suntrup_Ford_West', 'Suntrup Ford West',
            'Suntrup_Ford_Kirkwood', 'Suntrup Ford Kirkwood',
            'Joe_Machens_Toyota', 'Joe Machens Toyota',
            'Joe_Machens_Hyundai', 'Joe Machens Hyundai',
            'Thoroughbred_Ford', 'Thoroughbred Ford'
        ]
        
        for pattern in dealership_patterns:
            if pattern.lower() in path_str.lower():
                return pattern.replace('_', ' ')
                
        # Try to extract from directory structure
        parts = Path(path_str).parts
        for part in parts:
            if any(keyword in part.lower() for keyword in ['honda', 'bmw', 'ford', 'lincoln', 'toyota', 'hyundai']):
                return part.replace('_', ' ')
                
        return None
        
    def extract_date_from_path(self, file_path):
        """Extract date from file path or filename"""
        import re
        
        path_str = str(file_path)
        
        # Look for date patterns like 20250730, 2025-07-30, etc.
        date_patterns = [
            r'(\d{8})',  # YYYYMMDD
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, path_str)
            if matches:
                date_str = matches[-1]  # Take the last match
                try:
                    if len(date_str) == 8:  # YYYYMMDD
                        return datetime.strptime(date_str, '%Y%m%d').date()
                    elif '-' in date_str:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    elif '_' in date_str:
                        return datetime.strptime(date_str, '%Y_%m_%d').date()
                except ValueError:
                    continue
                    
        # Default to 7 days ago if no date found
        return (datetime.now() - timedelta(days=7)).date()
        
    def import_csv_file(self, csv_path):
        """Import VINs from a CSV file"""
        dealership = self.extract_dealership_from_path(csv_path)
        order_date = self.extract_date_from_path(csv_path)
        
        if not dealership:
            print(f"Skipping {csv_path.name}: Could not determine dealership")
            self.skipped_count += 1
            return
            
        print(f"Processing: {csv_path.name} -> {dealership} ({order_date})")
        
        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                vins = []
                
                for row in reader:
                    # Look for VIN in various column names
                    vin = None
                    for col_name in row.keys():
                        if col_name and 'vin' in col_name.lower():
                            vin = row[col_name]
                            break
                    
                    if vin and len(vin.strip()) >= 10:  # Basic VIN validation
                        # Clean VIN (remove prefixes like "NEW - ", "USED - ")
                        clean_vin = vin.replace('NEW - ', '').replace('USED - ', '').strip()
                        if len(clean_vin) == 17:  # Standard VIN length
                            vins.append(clean_vin)
                
                if vins:
                    self.import_vins_for_dealership(dealership, vins, order_date)
                    print(f"Imported {len(vins)} VINs from {csv_path.name}")
                else:
                    print(f"No valid VINs found in {csv_path.name}")
                    self.skipped_count += 1
                    
        except Exception as e:
            print(f"Error processing {csv_path.name}: {e}")
            self.error_count += 1
            
    def import_json_file(self, json_path):
        """Import VINs from a JSON file"""
        dealership = self.extract_dealership_from_path(json_path)
        order_date = self.extract_date_from_path(json_path)
        
        if not dealership:
            print(f"Skipping {json_path.name}: Could not determine dealership")
            self.skipped_count += 1
            return
            
        print(f"Processing: {json_path.name} -> {dealership} ({order_date})")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            vins = []
            
            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'vin' in item:
                        vins.append(item['vin'])
            elif isinstance(data, dict):
                if 'vehicles' in data:
                    for vehicle in data['vehicles']:
                        if 'vin' in vehicle:
                            vins.append(vehicle['vin'])
                elif 'vin' in data:
                    vins.append(data['vin'])
                    
            # Clean and validate VINs
            clean_vins = []
            for vin in vins:
                if isinstance(vin, str) and len(vin.strip()) == 17:
                    clean_vins.append(vin.strip().upper())
                    
            if clean_vins:
                self.import_vins_for_dealership(dealership, clean_vins, order_date)
                print(f"Imported {len(clean_vins)} VINs from {json_path.name}")
            else:
                print(f"No valid VINs found in {json_path.name}")
                self.skipped_count += 1
                
        except Exception as e:
            print(f"Error processing {json_path.name}: {e}")
            self.error_count += 1
            
    def import_vins_for_dealership(self, dealership_name, vins, order_date):
        """Import VINs for a specific dealership and date"""
        imported_this_batch = 0
        try:
            for vin in vins:
                try:
                    result = db_manager.execute_query("""
                        INSERT INTO vin_history (dealership_name, vin, order_date)
                        VALUES (%s, %s, %s)
                        ON CONFLICT ON CONSTRAINT vin_history_unique DO NOTHING
                        RETURNING id
                    """, (dealership_name, vin, order_date))
                    
                    if result:  # If a row was inserted
                        imported_this_batch += 1
                        
                except Exception as vin_error:
                    # Try without ON CONFLICT for databases that don't have the constraint yet
                    try:
                        db_manager.execute_query("""
                            INSERT INTO vin_history (dealership_name, vin, order_date)
                            VALUES (%s, %s, %s)
                        """, (dealership_name, vin, order_date))
                        imported_this_batch += 1
                    except Exception:
                        # Skip duplicate, likely already exists
                        pass
                
            self.imported_count += imported_this_batch
            
        except Exception as e:
            print(f"Database error importing VINs for {dealership_name}: {e}")
            self.error_count += 1
            
    def run_import(self):
        """Run the complete VIN history import process"""
        print("=" * 60)
        print("VIN HISTORY IMPORT SCRIPT")
        print("=" * 60)
        
        # Apply schema updates first
        self.apply_schema_updates()
        print()
        
        # Find all previous order files
        print("Searching for previous order files...")
        order_files = self.find_previous_orders()
        
        if not order_files:
            print("No order files found to import")
            return
            
        print(f"\nProcessing {len(order_files)} files...")
        print("-" * 40)
        
        for file_path in order_files:
            if file_path.suffix.lower() == '.csv':
                self.import_csv_file(file_path)
            elif file_path.suffix.lower() == '.json':
                self.import_json_file(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path.name}")
                self.skipped_count += 1
                
        # Print summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"VINs imported: {self.imported_count}")
        print(f"Files skipped: {self.skipped_count}")
        print(f"Errors: {self.error_count}")
        
        # Query final counts
        try:
            result = db_manager.execute_query("SELECT COUNT(*) as count FROM vin_history")
            total_vins = result[0]['count'] if result else 0
            print(f"Total VINs in history: {total_vins}")
            
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
                    
        except Exception as e:
            print(f"Error querying final counts: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("VIN History Import Script")
        print("Usage: python import_vin_history.py")
        print("\nThis script will:")
        print("1. Update database schema (add time_scraped column)")
        print("2. Search for previous order files (CSV/JSON)")
        print("3. Extract VINs and import them into vin_history table")
        print("4. Provide summary of imported data")
        return
        
    importer = VINHistoryImporter()
    importer.run_import()

if __name__ == "__main__":
    main()