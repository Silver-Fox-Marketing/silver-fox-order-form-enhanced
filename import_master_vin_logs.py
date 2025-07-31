#!/usr/bin/env python3
"""
Import Master VIN Logs from Excel Files
Processes all historical VIN logs to populate vin_history table
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent / "projects" / "minisforum_database_transfer" / "bulletproof_package"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(scripts_path))

from database_connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# VIN logs directory
VIN_LOGS_DIR = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS")

# Dealership name mapping from filename to database name
DEALERSHIP_MAPPING = {
    'AUDIRANCHOMIRAGE_VINLOG.xlsx': 'Audi Ranch Mirage',
    'AUFFENBERG_HYUNDAI_VINLOG.xlsx': 'Auffenberg Hyundai',
    'BMW_WEST_STL_VINLOG.xlsx': 'BMW of West St. Louis',
    'BOMM_CADILLAC_VINLOG.xlsx': 'Bommarito Cadillac',
    'BOMM_WCPO_VINLOG.xlsx': 'Bommarito West County',
    'COMOBMW_VINLOG.xlsx': 'Columbia BMW',
    'COMO_HONDA_VINLOG.xlsx': 'Columbia Honda',
    'DAVESINCLAIRSTPETERS_VINLOG.xlsx': 'Dave Sinclair Lincoln St Peters',
    'DSINCLAIRLINC_VINLOG.xlsx': 'Dave Sinclair Lincoln South',
    'FRANKLETA_HONDA_VINLOG.xlsx': 'Frank Leta Honda',
    'GLENDALE_VINLOG.xlsx': 'Glendale Chrysler Jeep',
    'HONDAofFRONTENAC_VINLOG.xlsx': 'Honda of Frontenac',
    'HW_KIA_VINLOG.xlsx': 'HW Kia',
    'INDIGOAUTOGROUP_VINLOG.xlsx': 'Indigo Auto Group',
    'JAGUARRANCHOMIRAGE_VINLOG.xlsx': 'Jaguar Ranch Mirage',
    'JM NISSAN LOG.xlsx': 'Joe Machens Nissan',
    'JMCDJR_VINLOG.xlsx': 'Joe Machens CDJR',
    'JMHYUNDAI_VINLOG.xlsx': 'Joe Machens Hyundai',
    'JM_TOYOTA_VINLOG.xlsx': 'Joe Machens Toyota',
    'KIACOMO_VINLOG.xlsx': 'Kia of Columbia',
    'LANDROVERRANCHOMIRAGE_VINLOG.xlsx': 'Land Rover Ranch Mirage',
    'Mini_of_St_Louis_VINLOG.xlsx': 'Mini of St. Louis',
    'PAPPAS_TOYOTA_VINLOG.xlsx': 'Pappas Toyota',
    'PORSCHESTL_VINLOG.xlsx': 'Porsche St. Louis',
    'PUNDMANN_VINLOG.xlsx': 'Pundmann Ford',
    'RDCADILLAC_VINLOG.xlsx': 'Rusty Drew Cadillac',
    'RDCHEVY_VINLOG.xlsx': 'Rusty Drew Chevrolet',
    'SERRAHONDA_VINLOG.xlsx': 'Serra Honda of O\'Fallon',
    'SOCODCJR_VINLOG.xlsx': 'South County Auto',
    'SPIRIT_LEXUS_VINLOG.xlsx': 'Spirit Lexus',
    'SUNTRUP_BGMC_VINLOG.xlsx': 'Suntrup Buick GMC',
    'SUNTRUP_FORD_KIRKWOOD_VINLOG.xlsx': 'Suntrup Ford Kirkwood',
    'SUNTRUP_FORD_WESTPORT_VINLOG.xlsx': 'Suntrup Ford West',
    'SUNTRUP_HYUNDAI_VINLOG.xlsx': 'Suntrup Hyundai South',
    'SUNTRUP_KIA_VINLOG.xlsx': 'Suntrup Kia South',
    'TBRED_FORD_VINLOG.xlsx': 'Thoroughbred Ford',
    'TOMSTEHOUWER_VINLOG.xlsx': 'Tom Stehouwer Auto',
    'TWINCITYTOYO_VINLOG.xlsx': 'Twin City Toyota',
    'VOLVO_WC_VINLOG.xlsx': 'WC Volvo Cars',
    'WEBER_VINLOG.xlsx': 'Weber Chevrolet'
}

def normalize_vehicle_type(vehicle_type: str) -> str:
    """Normalize vehicle type to standard categories"""
    if not vehicle_type or pd.isna(vehicle_type):
        return 'unknown'
        
    vehicle_type = str(vehicle_type).lower().strip()
    
    if any(keyword in vehicle_type for keyword in ['new', 'brand new']):
        return 'new'
    elif any(keyword in vehicle_type for keyword in ['certified', 'cpo', 'pre-owned']):
        return 'certified'
    elif any(keyword in vehicle_type for keyword in ['used', 'pre owned']):
        return 'used'
    else:
        return 'unknown'

def extract_date_from_filename_or_content(filepath: Path, df: pd.DataFrame) -> datetime:
    """Extract date from filename or Excel content"""
    
    # Try to find date columns in the Excel file
    date_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(date_word in col_lower for date_word in ['date', 'processed', 'created', 'scraped', 'order']):
            date_columns.append(col)
    
    # If we found date columns, use the most recent date
    if date_columns and len(df) > 0:
        for col in date_columns:
            try:
                # Try to parse dates from the column
                dates = pd.to_datetime(df[col], errors='coerce').dropna()
                if len(dates) > 0:
                    # Use the most recent date from this column
                    return dates.max().to_pydatetime()
            except:
                continue
    
    # Fallback: try to extract date from filename
    filename = filepath.stem
    
    # Look for date patterns in filename (YYYY-MM-DD, MM-DD-YYYY, etc.)
    import re
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})-(\d{1,2})-(\d{4})',
        r'(\d{4})(\d{2})(\d{2})',
        r'(\d{2})(\d{2})(\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # Year first
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # Month first or day first
                    if int(groups[2]) > 31:  # Year is last
                        month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    else:  # Year is first (unlikely but possible)
                        year, month, day = int(groups[2]), int(groups[0]), int(groups[1])
                
                return datetime(year, month, day)
            except:
                continue
    
    # Ultimate fallback: use file modification time
    return datetime.fromtimestamp(filepath.stat().st_mtime)

def import_vin_log_file(filepath: Path) -> Dict[str, Any]:
    """Import a single VIN log Excel file"""
    
    filename = filepath.name
    dealership_name = DEALERSHIP_MAPPING.get(filename, filename.replace('_VINLOG.xlsx', '').replace('_', ' '))
    
    logger.info(f"Processing {filename} -> {dealership_name}")
    
    try:
        # Read Excel file
        df = pd.read_excel(filepath)
        
        if df.empty:
            return {'success': False, 'error': 'Empty file', 'dealership': dealership_name}
        
        logger.info(f"Found {len(df)} rows in {filename}")
        
        # Extract order date
        order_date = extract_date_from_filename_or_content(filepath, df)
        logger.info(f"Using order date: {order_date.strftime('%Y-%m-%d')}")
        
        # Find VIN column
        vin_column = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'vin' in col_lower:
                vin_column = col
                break
        
        if not vin_column:
            # Try common VIN-like columns
            for col in df.columns:
                col_lower = str(col).lower()
                if any(vin_word in col_lower for vin_word in ['stock', 'id', 'serial']):
                    vin_column = col
                    break
        
        if not vin_column:
            return {'success': False, 'error': 'No VIN column found', 'dealership': dealership_name}
        
        # Find vehicle type column
        type_column = None
        for col in df.columns:
            col_lower = str(col).lower()
            if any(type_word in col_lower for type_word in ['type', 'condition', 'status', 'category']):
                type_column = col
                break
        
        # Process VINs
        vins_imported = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                vin = row[vin_column]
                if pd.isna(vin) or not vin:
                    continue
                
                vin = str(vin).strip()
                if len(vin) < 5:  # Skip obviously invalid VINs
                    continue
                
                # Get vehicle type
                vehicle_type = 'unknown'
                if type_column and not pd.isna(row[type_column]):
                    vehicle_type = normalize_vehicle_type(row[type_column])
                
                # Insert into database
                try:
                    db_manager.execute_query("""
                        INSERT INTO vin_history (dealership_name, vin, vehicle_type, order_date, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (dealership_name, vin, order_date) DO UPDATE SET
                        vehicle_type = EXCLUDED.vehicle_type,
                        created_at = CURRENT_TIMESTAMP
                    """, (dealership_name, vin, vehicle_type, order_date.date(), datetime.now()))
                    
                    vins_imported += 1
                    
                except Exception as db_error:
                    errors.append(f"Row {idx}: {str(db_error)}")
                    
            except Exception as row_error:
                errors.append(f"Row {idx}: {str(row_error)}")
        
        return {
            'success': True,
            'dealership': dealership_name,
            'vins_imported': vins_imported,
            'total_rows': len(df),
            'order_date': order_date.strftime('%Y-%m-%d'),
            'errors': errors[:5]  # Show first 5 errors only
        }
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")
        return {'success': False, 'error': str(e), 'dealership': dealership_name}

def import_all_vin_logs():
    """Import all VIN log files"""
    
    logger.info(f"=== IMPORTING MASTER VIN LOGS ===")
    logger.info(f"Source directory: {VIN_LOGS_DIR}")
    
    if not VIN_LOGS_DIR.exists():
        logger.error(f"VIN logs directory not found: {VIN_LOGS_DIR}")
        return False
    
    # Get all Excel files
    excel_files = list(VIN_LOGS_DIR.glob("*.xlsx"))
    logger.info(f"Found {len(excel_files)} Excel files to process")
    
    if len(excel_files) == 0:
        logger.error("No Excel files found in VIN logs directory")
        return False
    
    # Process each file
    results = []
    total_vins = 0
    successful_imports = 0
    
    for filepath in excel_files:
        result = import_vin_log_file(filepath)
        results.append(result)
        
        if result['success']:
            successful_imports += 1
            total_vins += result['vins_imported']
            logger.info(f"✅ {result['dealership']}: {result['vins_imported']} VINs imported")
        else:
            logger.error(f"❌ {result['dealership']}: {result['error']}")
    
    # Summary
    logger.info(f"\n=== IMPORT SUMMARY ===")
    logger.info(f"Files processed: {len(excel_files)}")
    logger.info(f"Successful imports: {successful_imports}")
    logger.info(f"Total VINs imported: {total_vins}")
    logger.info(f"Dealerships with data: {len([r for r in results if r['success']])}")
    
    # Show successful dealerships
    logger.info(f"\n=== SUCCESSFUL IMPORTS ===")
    for result in results:
        if result['success']:
            errors_info = f" ({len(result['errors'])} errors)" if result['errors'] else ""
            logger.info(f"{result['dealership']}: {result['vins_imported']} VINs from {result['order_date']}{errors_info}")
    
    # Show failed imports
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        logger.info(f"\n=== FAILED IMPORTS ===")
        for result in failed_results:
            logger.error(f"{result['dealership']}: {result['error']}")
    
    return True

def verify_import():
    """Verify the VIN history import"""
    
    logger.info(f"\n=== VERIFYING VIN HISTORY IMPORT ===")
    
    try:
        # Count total VINs by dealership
        result = db_manager.execute_query("""
            SELECT dealership_name, vehicle_type, COUNT(*) as vin_count
            FROM vin_history 
            GROUP BY dealership_name, vehicle_type
            ORDER BY dealership_name, vehicle_type
        """)
        
        if result:
            logger.info(f"VIN History Status:")
            current_dealer = None
            dealer_total = 0
            
            for row in result:
                if current_dealer != row['dealership_name']:
                    if current_dealer:
                        logger.info(f"  {current_dealer} TOTAL: {dealer_total} VINs")
                    current_dealer = row['dealership_name']
                    dealer_total = 0
                    logger.info(f"\n{current_dealer}:")
                
                vtype = row['vehicle_type'] or 'unknown'
                count = row['vin_count']
                dealer_total += count
                logger.info(f"  {vtype}: {count} VINs")
            
            if current_dealer:
                logger.info(f"  {current_dealer} TOTAL: {dealer_total} VINs")
        
        # Overall statistics
        total_result = db_manager.execute_query("""
            SELECT COUNT(*) as total_vins, 
                   COUNT(DISTINCT dealership_name) as total_dealerships,
                   MIN(order_date) as earliest_date,
                   MAX(order_date) as latest_date
            FROM vin_history
        """)
        
        if total_result:
            stats = total_result[0]
            logger.info(f"\n=== OVERALL STATISTICS ===")
            logger.info(f"Total VINs: {stats['total_vins']}")
            logger.info(f"Total Dealerships: {stats['total_dealerships']}")
            logger.info(f"Date Range: {stats['earliest_date']} to {stats['latest_date']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying import: {e}")
        return False

if __name__ == "__main__":
    logger.info("MASTER VIN LOG IMPORT STARTING")
    logger.info("=" * 50)
    
    # Import all VIN logs
    if import_all_vin_logs():
        # Verify the import
        verify_import()
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ MASTER VIN LOG IMPORT COMPLETED!")
        logger.info("Your enhanced VIN logic now has complete historical context")
        logger.info("Cross-dealership and relisted vehicle scenarios will be handled intelligently")
        logger.info("=" * 50)
    else:
        logger.error("❌ VIN log import failed")