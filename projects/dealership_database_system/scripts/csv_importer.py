"""
CSV import script for dealership data
Handles bulk import of CSV files with data validation and normalization
"""
import csv
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
import glob
from pathlib import Path
import pandas as pd
from database_connection import db_manager
from database_config import (
    config, CONDITION_MAPPING, CSV_COLUMNS, 
    REQUIRED_COLUMNS, NUMERIC_COLUMNS, DATE_COLUMNS
)

logger = logging.getLogger(__name__)

class CSVImporter:
    """Handles CSV data import with validation and normalization"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.import_stats = {
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'errors': []
        }
    
    def normalize_condition(self, type_value: str, status_value: str) -> str:
        """Normalize vehicle condition based on type and status"""
        if pd.isna(type_value) and pd.isna(status_value):
            return 'onlot'  # Default
        
        # Check type first
        type_str = str(type_value).lower().strip() if not pd.isna(type_value) else ''
        if type_str in CONDITION_MAPPING:
            return CONDITION_MAPPING[type_str]
        
        # Check status if type doesn't match
        status_str = str(status_value).lower().strip() if not pd.isna(status_value) else ''
        if status_str in CONDITION_MAPPING:
            return CONDITION_MAPPING[status_str]
        
        return 'onlot'  # Default if no match
    
    def validate_row(self, row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single row of data"""
        # Check required fields
        for col in REQUIRED_COLUMNS:
            if col not in row or pd.isna(row[col]) or str(row[col]).strip() == '':
                return False, f"Missing required field: {col}"
        
        # Validate VIN length and format (should be 17 alphanumeric characters)
        vin = str(row['vin']).strip().upper()
        if len(vin) != 17:
            return False, f"Invalid VIN length: {len(vin)} (should be 17)"
        
        # Check VIN contains only valid characters (no I, O, Q)
        if not vin.replace('I', '').replace('O', '').replace('Q', '').isalnum():
            return False, f"Invalid VIN characters (contains invalid chars)"
        
        # Validate year range
        if 'year' in row and not pd.isna(row['year']):
            try:
                year = int(row['year'])
                current_year = datetime.now().year
                if year < 1980 or year > current_year + 2:
                    return False, f"Invalid year: {year} (must be between 1980 and {current_year + 2})"
            except (ValueError, TypeError):
                pass  # Will be handled in numeric cleaning
        
        # Validate price is reasonable
        if 'price' in row and not pd.isna(row['price']):
            try:
                price = self.clean_numeric(row['price'])
                if price is not None and (price < 0 or price > 500000):
                    return False, f"Invalid price: ${price} (must be between $0 and $500,000)"
            except:
                pass  # Will be handled in numeric cleaning
        
        return True, None
    
    def clean_numeric(self, value) -> Optional[float]:
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '':
            return None
        
        # Remove common currency symbols and commas
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def clean_date(self, value) -> Optional[date]:
        """Clean and convert date values"""
        if pd.isna(value) or value == '':
            return None
        
        # Try common date formats
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def import_csv_file(self, file_path: str, dealership_name: str = None) -> Dict:
        """Import a single CSV file"""
        logger.info(f"Importing CSV file: {file_path}")
        
        # Extract dealership name from filename if not provided
        if not dealership_name:
            dealership_name = Path(file_path).stem
        
        try:
            # Read CSV with pandas for better handling of various formats
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            
            # Ensure all expected columns exist
            for col in CSV_COLUMNS:
                if col not in df.columns:
                    df[col] = ''
            
            # Add dealership location if not present
            if 'location' not in df.columns or df['location'].str.strip().eq('').all():
                df['location'] = dealership_name
            
            raw_data = []
            normalized_data = []
            vin_history_data = []
            
            for idx, row in df.iterrows():
                self.import_stats['total_rows'] += 1
                
                # Validate row
                is_valid, error_msg = self.validate_row(row)
                if not is_valid:
                    self.import_stats['skipped_rows'] += 1
                    self.import_stats['errors'].append(f"Row {idx + 1}: {error_msg}")
                    continue
                
                # Prepare raw data tuple
                raw_tuple = (
                    str(row['vin']).strip(),
                    str(row['stock']).strip(),
                    row.get('type', ''),
                    int(row['year']) if row.get('year') and str(row['year']).isdigit() else None,
                    row.get('make', ''),
                    row.get('model', ''),
                    row.get('trim', ''),
                    row.get('ext_color', ''),
                    row.get('status', ''),
                    self.clean_numeric(row.get('price')),
                    row.get('body_style', ''),
                    row.get('fuel_type', ''),
                    self.clean_numeric(row.get('msrp')),
                    self.clean_date(row.get('date_in_stock')),
                    row.get('street_address', ''),
                    row.get('locality', ''),
                    row.get('postal_code', ''),
                    row.get('region', ''),
                    row.get('country', ''),
                    row.get('location', dealership_name),
                    row.get('vehicle_url', '')
                )
                raw_data.append(raw_tuple)
            
            # Bulk insert raw data
            if raw_data:
                raw_columns = [
                    'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
                    'ext_color', 'status', 'price', 'body_style', 'fuel_type',
                    'msrp', 'date_in_stock', 'street_address', 'locality',
                    'postal_code', 'region', 'country', 'location', 'vehicle_url'
                ]
                
                rows_inserted = self.db.execute_batch_insert(
                    'raw_vehicle_data', 
                    raw_columns, 
                    raw_data
                )
                
                self.import_stats['imported_rows'] += rows_inserted
                
                # Get the inserted raw data IDs for normalization
                today = date.today()
                raw_records = self.db.execute_query(
                    """
                    SELECT id, vin, stock, type, year, make, model, trim, 
                           status, price, msrp, date_in_stock, location, vehicle_url
                    FROM raw_vehicle_data
                    WHERE location = %s AND import_date = %s
                    """,
                    (dealership_name, today)
                )
                
                # Prepare normalized data
                for record in raw_records:
                    condition = self.normalize_condition(record['type'], record['status'])
                    
                    # Skip off-lot vehicles unless specifically configured
                    if condition == 'offlot':
                        continue
                    
                    normalized_tuple = (
                        record['id'],  # raw_data_id
                        record['vin'],
                        record['stock'],
                        condition,
                        record['year'],
                        record['make'],
                        record['model'],
                        record['trim'],
                        record['status'],
                        record['price'],
                        record['msrp'],
                        record['date_in_stock'],
                        record['location'],
                        record['vehicle_url']
                    )
                    normalized_data.append(normalized_tuple)
                    
                    # VIN history entry
                    vin_history_data.append((
                        record['vin'],
                        record['location'],
                        today,
                        record['id']
                    ))
                
                # Upsert normalized data
                if normalized_data:
                    norm_columns = [
                        'raw_data_id', 'vin', 'stock', 'vehicle_condition',
                        'year', 'make', 'model', 'trim', 'status', 'price',
                        'msrp', 'date_in_stock', 'location', 'vehicle_url'
                    ]
                    
                    self.db.upsert_data(
                        'normalized_vehicle_data',
                        norm_columns,
                        normalized_data,
                        conflict_columns=['vin', 'location'],
                        update_columns=['stock', 'vehicle_condition', 'price', 
                                      'status', 'last_seen_date', 'updated_at']
                    )
                
                # Insert VIN history
                if vin_history_data:
                    self.db.execute_batch_insert(
                        'vin_history',
                        ['vin', 'dealership_name', 'scan_date', 'raw_data_id'],
                        vin_history_data
                    )
            
            logger.info(f"Import completed for {dealership_name}: "
                       f"{self.import_stats['imported_rows']} rows imported")
            
            return self.import_stats
            
        except Exception as e:
            logger.error(f"Error importing {file_path}: {e}")
            self.import_stats['errors'].append(f"File error: {str(e)}")
            raise
    
    def import_directory(self, directory_path: str) -> Dict:
        """Import all CSV files from a directory"""
        csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
        
        logger.info(f"Found {len(csv_files)} CSV files to import")
        
        overall_stats = {
            'total_files': len(csv_files),
            'successful_files': 0,
            'failed_files': 0,
            'total_rows_imported': 0
        }
        
        for csv_file in csv_files:
            try:
                self.import_stats = {
                    'total_rows': 0,
                    'imported_rows': 0,
                    'skipped_rows': 0,
                    'errors': []
                }
                
                stats = self.import_csv_file(csv_file)
                overall_stats['successful_files'] += 1
                overall_stats['total_rows_imported'] += stats['imported_rows']
                
            except Exception as e:
                logger.error(f"Failed to import {csv_file}: {e}")
                overall_stats['failed_files'] += 1
        
        # Run maintenance after bulk import
        logger.info("Running VACUUM ANALYZE on tables...")
        self.db.vacuum_analyze('raw_vehicle_data')
        self.db.vacuum_analyze('normalized_vehicle_data')
        
        return overall_stats
    
    def update_vin_scan_counts(self):
        """Update VIN scan counts in normalized data"""
        query = """
            UPDATE normalized_vehicle_data n
            SET vin_scan_count = (
                SELECT COUNT(DISTINCT scan_date)
                FROM vin_history v
                WHERE v.vin = n.vin AND v.dealership_name = n.location
            )
            WHERE last_seen_date = CURRENT_DATE
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            updated = cursor.rowcount
            logger.info(f"Updated scan counts for {updated} vehicles")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import CSV files to dealership database')
    parser.add_argument('path', help='Path to CSV file or directory')
    parser.add_argument('--dealership', help='Dealership name (if not in filename)')
    parser.add_argument('--update-counts', action='store_true', 
                       help='Update VIN scan counts after import')
    
    args = parser.parse_args()
    
    importer = CSVImporter()
    
    try:
        if os.path.isfile(args.path):
            stats = importer.import_csv_file(args.path, args.dealership)
            print(f"\nImport completed:")
            print(f"  Total rows: {stats['total_rows']}")
            print(f"  Imported: {stats['imported_rows']}")
            print(f"  Skipped: {stats['skipped_rows']}")
            if stats['errors']:
                print(f"  Errors: {len(stats['errors'])}")
        
        elif os.path.isdir(args.path):
            stats = importer.import_directory(args.path)
            print(f"\nBulk import completed:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Successful: {stats['successful_files']}")
            print(f"  Failed: {stats['failed_files']}")
            print(f"  Total rows imported: {stats['total_rows_imported']}")
        
        else:
            print(f"Error: {args.path} is not a valid file or directory")
            return
        
        if args.update_counts:
            importer.update_vin_scan_counts()
        
    except Exception as e:
        print(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    main()