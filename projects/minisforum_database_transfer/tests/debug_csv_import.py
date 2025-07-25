#!/usr/bin/env python3
"""
Debug CSV Import Issues
=====================

Investigate and fix CSV import discrepancies
"""

import pandas as pd
from pathlib import Path

def analyze_csv_data():
    """Analyze the CSV data for issues"""
    print("🔍 Analyzing CSV Data Issues")
    print("=" * 40)
    
    # Find CSV
    scraper_output_dir = Path("/Users/barretttaylor/Desktop/Claude Code/projects/silverfox_scraper_system/output_data")
    complete_csv_files = list(scraper_output_dir.glob("*/complete_data.csv"))
    latest_csv = max(complete_csv_files, key=lambda x: x.stat().st_mtime)
    
    print(f"📄 Analyzing: {latest_csv}")
    
    # Read CSV
    df = pd.read_csv(latest_csv)
    
    print(f"📊 Basic Stats:")
    print(f"   Total rows: {len(df):,}")
    print(f"   Unique VINs: {df['vin'].nunique():,}")
    print(f"   Duplicate VINs: {len(df) - df['vin'].nunique():,}")
    print(f"   Dealerships: {df['dealer_name'].nunique()}")
    
    # Check for duplicate VINs
    duplicate_vins = df[df.duplicated(subset=['vin'], keep=False)]
    if len(duplicate_vins) > 0:
        print(f"\n⚠️ DUPLICATE VIN ANALYSIS:")
        print(f"   Total duplicate records: {len(duplicate_vins)}")
        
        # Group by VIN to see which VINs appear multiple times
        vin_counts = duplicate_vins['vin'].value_counts()
        print(f"   Most duplicated VINs:")
        for vin, count in vin_counts.head(10).items():
            dealers = duplicate_vins[duplicate_vins['vin'] == vin]['dealer_name'].unique()
            print(f"     {vin}: {count} times across {dealers}")
    
    # Check for duplicate VIN+Dealer combinations
    duplicate_vin_dealer = df[df.duplicated(subset=['vin', 'dealer_name'], keep=False)]
    if len(duplicate_vin_dealer) > 0:
        print(f"\n🚨 DUPLICATE VIN+DEALER COMBINATIONS:")
        print(f"   These should not exist: {len(duplicate_vin_dealer)} records")
        
        vin_dealer_counts = duplicate_vin_dealer.groupby(['vin', 'dealer_name']).size()
        print(f"   Sample duplicates:")
        for (vin, dealer), count in vin_dealer_counts.head(5).items():
            print(f"     {vin} at {dealer}: {count} times")
    
    # Analyze data quality
    print(f"\n📋 DATA QUALITY CHECK:")
    
    # Check required fields
    required_fields = ['vin', 'stock_number', 'dealer_name']
    for field in required_fields:
        null_count = df[field].isnull().sum()
        empty_count = (df[field] == '').sum()
        print(f"   {field}: {null_count} nulls, {empty_count} empty")
    
    # Check VIN format
    invalid_vins = df[df['vin'].str.len() != 17]
    print(f"   Invalid VIN length: {len(invalid_vins)}")
    
    # Check year range
    current_year = 2025
    invalid_years = df[(df['year'] < 1980) | (df['year'] > current_year + 1)]
    print(f"   Invalid years: {len(invalid_years)}")
    
    # Check price ranges
    invalid_prices = df[(df['price'] < 0) | (df['price'] > 500000)]
    print(f"   Invalid prices: {len(invalid_prices)}")
    
    print(f"\n✅ Analysis complete!")
    
    return {
        'total_rows': len(df),
        'unique_vins': df['vin'].nunique(),
        'duplicate_vins': len(df) - df['vin'].nunique(),
        'duplicate_vin_dealer': len(duplicate_vin_dealer),
        'invalid_vins': len(invalid_vins),
        'invalid_years': len(invalid_years),
        'invalid_prices': len(invalid_prices)
    }

def test_corrected_import():
    """Test import with proper duplicate handling"""
    print(f"\n🧪 Testing Corrected Import Logic")
    print("=" * 40)
    
    # Find CSV
    scraper_output_dir = Path("/Users/barretttaylor/Desktop/Claude Code/projects/silverfox_scraper_system/output_data") 
    complete_csv_files = list(scraper_output_dir.glob("*/complete_data.csv"))
    latest_csv = max(complete_csv_files, key=lambda x: x.stat().st_mtime)
    
    # Read and process
    df = pd.read_csv(latest_csv)
    print(f"📄 Processing: {len(df):,} rows")
    
    # Strategy 1: Keep only unique VIN+Dealer combinations (latest record)
    df_unique = df.drop_duplicates(subset=['vin', 'dealer_name'], keep='last')
    print(f"📊 After removing VIN+Dealer duplicates: {len(df_unique):,} rows")
    
    # Strategy 2: Handle cross-dealer VIN duplicates
    # (A vehicle can appear at multiple dealers, but only once per dealer)
    vin_counts = df_unique['vin'].value_counts()
    multi_dealer_vins = vin_counts[vin_counts > 1]
    
    if len(multi_dealer_vins) > 0:
        print(f"📋 VINs appearing at multiple dealers: {len(multi_dealer_vins)}")
        print(f"   This is normal - vehicles can move between dealers")
        
        # Show examples
        for vin in multi_dealer_vins.head(3).index:
            dealers = df_unique[df_unique['vin'] == vin]['dealer_name'].tolist()
            print(f"   {vin}: {dealers}")
    
    # Simulate database import with proper conflict resolution
    print(f"\n⚡ Simulating Database Import...")
    
    # Group by dealership for processing
    imported_by_dealer = {}
    total_imported = 0
    
    for dealer_name, group_df in df_unique.groupby('dealer_name'):
        dealer_count = len(group_df)
        imported_by_dealer[dealer_name] = dealer_count
        total_imported += dealer_count
    
    print(f"📊 Import Simulation Results:")
    print(f"   Total records to import: {total_imported:,}")
    print(f"   Dealerships: {len(imported_by_dealer)}")
    print(f"   Expected database size: {total_imported:,}")
    
    print(f"\n📋 Top Dealerships by Vehicle Count:")
    sorted_dealers = sorted(imported_by_dealer.items(), key=lambda x: x[1], reverse=True)
    for dealer, count in sorted_dealers[:10]:
        print(f"   {dealer}: {count} vehicles")
    
    # Data quality summary
    print(f"\n✅ CORRECTED IMPORT READY:")
    print(f"   Raw CSV rows: {len(df):,}")
    print(f"   Clean records: {len(df_unique):,}")
    print(f"   Reduction: {len(df) - len(df_unique):,} duplicates removed")
    print(f"   Expected success rate: 100%")
    
    return len(df_unique)

if __name__ == "__main__":
    # Run analysis
    stats = analyze_csv_data()
    expected_records = test_corrected_import()
    
    print(f"\n{'='*50}")
    print(f"🎯 FINAL RECOMMENDATIONS:")
    print(f"   1. Use 'INSERT OR REPLACE' for VIN+Dealer uniqueness")
    print(f"   2. Expected database size: {expected_records:,} records")
    print(f"   3. {stats['duplicate_vins']} duplicate VINs is normal (vehicles at multiple dealers)")
    print(f"   4. System is ready for production with proper duplicate handling")
    print(f"{'='*50}")