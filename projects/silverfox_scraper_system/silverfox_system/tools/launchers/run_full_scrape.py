#!/usr/bin/env python3
"""
Full Production Scrape - Generate comparison data
Run full scrape of all 44 dealerships and compare to reference data
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    from batch_scraper import BatchScraper
    from normalizer import VehicleDataNormalizer
    from dealerships.verified_working_dealerships import get_production_ready_dealerships
    DEALERSHIP_CONFIGS = get_production_ready_dealerships()
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def run_full_scrape():
    """Run full production scrape"""
    print("🚗 SILVER FOX MARKETING - FULL PRODUCTION SCRAPE")
    print("=" * 60)
    print(f"📊 Total dealerships: {len(DEALERSHIP_CONFIGS)}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize components
    batch_scraper = BatchScraper()
    normalizer = VehicleDataNormalizer()
    
    all_results = []
    successful_dealerships = 0
    failed_dealerships = 0
    start_time = time.time()
    
    # Process each dealership
    for i, (dealer_id, config) in enumerate(DEALERSHIP_CONFIGS.items(), 1):
        print(f"[{i:2d}/{len(DEALERSHIP_CONFIGS)}] 🔄 {config['name']} ({config['brand']})...")
        
        try:
            # Run individual scraper
            dealer_result = batch_scraper._scrape_single(dealer_id, max_vehicles=100)
            dealer_results = dealer_result.get('vehicles', [])
            
            if dealer_results and len(dealer_results) > 0:
                all_results.extend(dealer_results)
                successful_dealerships += 1
                print(f"         ✅ Found {len(dealer_results)} vehicles")
            else:
                failed_dealerships += 1
                print(f"         ⚠️  No vehicles found")
                
        except Exception as e:
            failed_dealerships += 1
            print(f"         ❌ Error: {str(e)[:80]}...")
        
        # Brief delay between dealerships
        time.sleep(1)
    
    elapsed_time = time.time() - start_time
    
    print()
    print("🔄 NORMALIZING DATA...")
    
    # Normalize all results
    if all_results:
        df = pd.DataFrame(all_results)
        print(f"📊 Raw data: {len(df)} vehicles")
        
        normalized_df = normalizer.normalize_dataframe(df)
        print(f"📊 Normalized: {len(normalized_df)} vehicles")
        
        # Save results
        output_file = f"full_scrape_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        normalized_df.to_csv(output_file, index=False)
        
        print()
        print("✅ SCRAPING COMPLETED")
        print("=" * 60)
        print(f"📈 Success rate: {successful_dealerships}/{len(DEALERSHIP_CONFIGS)} ({successful_dealerships/len(DEALERSHIP_CONFIGS)*100:.1f}%)")
        print(f"📊 Total vehicles: {len(normalized_df)}")
        print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
        print(f"💾 Saved to: {output_file}")
        
        return normalized_df, output_file
    
    else:
        print("❌ No data collected")
        return None, None

def compare_to_reference(new_data_file):
    """Compare new scrape results to reference data"""
    print()
    print("🔍 COMPARING TO REFERENCE DATA")
    print("=" * 60)
    
    # Load reference data
    reference_file = "docs/business-context/complete_data.csv"
    
    try:
        reference_df = pd.read_csv(reference_file)
        print(f"📂 Reference data: {len(reference_df)} vehicles")
        print(f"📅 Reference columns: {list(reference_df.columns)}")
        
        # Load new data
        new_df = pd.read_csv(new_data_file)
        print(f"📂 New data: {len(new_df)} vehicles")
        print(f"📅 New columns: {list(new_df.columns)}")
        
        # Basic comparison
        print()
        print("📊 COMPARISON RESULTS:")
        print(f"   Reference vehicles: {len(reference_df):,}")
        print(f"   New scrape vehicles: {len(new_df):,}")
        print(f"   Difference: {len(new_df) - len(reference_df):+,}")
        print(f"   Coverage: {len(new_df)/len(reference_df)*100:.1f}%")
        
        # Column comparison
        ref_cols = set(reference_df.columns)
        new_cols = set(new_df.columns)
        
        print()
        print("📋 COLUMN ANALYSIS:")
        print(f"   Reference columns: {len(ref_cols)}")
        print(f"   New columns: {len(new_cols)}")
        
        missing_cols = ref_cols - new_cols
        if missing_cols:
            print(f"   Missing columns: {missing_cols}")
        
        extra_cols = new_cols - ref_cols
        if extra_cols:
            print(f"   Extra columns: {extra_cols}")
        
        common_cols = ref_cols & new_cols
        print(f"   Common columns: {len(common_cols)}")
        
        # Data quality comparison
        print()
        print("🔬 DATA QUALITY ANALYSIS:")
        
        for col in ['vin', 'year', 'make', 'model']:
            if col in common_cols:
                ref_non_null = reference_df[col].notna().sum()
                new_non_null = new_df[col].notna().sum()
                print(f"   {col.capitalize()} completeness: {ref_non_null:,} → {new_non_null:,}")
        
        # Brand distribution comparison
        if 'make' in common_cols:
            print()
            print("🏢 BRAND DISTRIBUTION:")
            ref_brands = reference_df['make'].value_counts().head(5)
            new_brands = new_df['make'].value_counts().head(5)
            
            print("   Reference top 5:")
            for brand, count in ref_brands.items():
                print(f"     {brand}: {count:,}")
            
            print("   New scrape top 5:")
            for brand, count in new_brands.items():
                print(f"     {brand}: {count:,}")
        
        return {
            'reference_count': len(reference_df),
            'new_count': len(new_df),
            'coverage_percentage': len(new_df)/len(reference_df)*100,
            'reference_columns': len(ref_cols),
            'new_columns': len(new_cols),
            'common_columns': len(common_cols)
        }
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return None

def main():
    """Run full scrape and comparison"""
    # Run the scrape
    new_data, output_file = run_full_scrape()
    
    if new_data is not None and output_file:
        # Compare to reference
        comparison = compare_to_reference(output_file)
        
        if comparison:
            print()
            print("🎯 FINAL ASSESSMENT")
            print("=" * 60)
            
            if comparison['coverage_percentage'] >= 80:
                print("✅ EXCELLENT: New scrape achieves good coverage")
            elif comparison['coverage_percentage'] >= 60:
                print("⚠️  MODERATE: New scrape has acceptable coverage")
            else:
                print("❌ POOR: New scrape has low coverage")
            
            print(f"📊 Coverage: {comparison['coverage_percentage']:.1f}%")
            print(f"🔧 System working: {comparison['new_count'] > 1000}")

if __name__ == "__main__":
    main()