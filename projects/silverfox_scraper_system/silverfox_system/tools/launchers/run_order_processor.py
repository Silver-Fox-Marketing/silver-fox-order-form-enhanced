#!/usr/bin/env python3
"""
Order Processing Control Center
Enhanced order processing system that goes beyond Google Sheets limitations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.order_processor import OrderProcessor, OrderConfig, create_order_processor
from scraper.normalizer import create_vehicle_normalizer
from datetime import datetime
import pandas as pd
import json

def run_complete_workflow(raw_csv_file: str = None, output_dir: str = "output_data"):
    """
    Complete workflow: Raw CSV → Normalized CSV → Order Processing
    """
    print("🚀 Starting Complete Order Processing Workflow")
    print("=" * 60)
    
    # Step 1: Normalize raw data if provided
    if raw_csv_file and os.path.exists(raw_csv_file):
        print(f"📊 Step 1: Normalizing data from {raw_csv_file}")
        
        normalizer = create_vehicle_normalizer()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        normalized_file = f"{output_dir}/normalized_{timestamp}.csv"
        
        os.makedirs(output_dir, exist_ok=True)
        
        normalization_result = normalizer.normalize_csv_file(raw_csv_file, normalized_file)
        print(f"✅ Normalization complete: {normalization_result['normalized_count']} records")
        print(f"📄 Normalized file: {normalized_file}")
    else:
        # Use existing normalized file
        normalized_files = [f for f in os.listdir(output_dir) if f.startswith('normalized_') and f.endswith('.csv')]
        if normalized_files:
            normalized_file = os.path.join(output_dir, sorted(normalized_files)[-1])
            print(f"📄 Using existing normalized file: {normalized_file}")
        else:
            print("❌ No raw CSV provided and no existing normalized files found")
            return
    
    # Step 2: Initialize Order Processor
    print(f"\n🗄️ Step 2: Initializing Order Processor Database")
    processor = create_order_processor()
    
    # Step 3: Import normalized data
    print(f"📥 Step 3: Importing normalized data to database")
    import_result = processor.import_normalized_data(normalized_file)
    print(f"✅ Import complete: {import_result['inserted_records']} records in database")
    
    # Step 4: Generate inventory summary
    print(f"\n📈 Step 4: Generating inventory summary")
    summary = processor.get_dealership_inventory_summary()
    print(f"🏪 Total dealerships: {summary['overall_stats']['dealership_count']}")
    print(f"🚗 Total vehicles: {summary['overall_stats']['total_vehicles']}")
    print(f"💰 Average price: ${summary['overall_stats']['avg_price']:,.2f}")
    
    # Step 5: Create sample orders
    print(f"\n📋 Step 5: Creating sample orders")
    
    # Create a comparative order
    comparative_config = OrderConfig(
        order_id=f"comparative_{timestamp}",
        order_type="comparative",
        dealerships=[],  # All dealerships
        filters={
            "min_price": 20000,
            "max_price": 50000
        }
    )
    processor.create_order(comparative_config)
    comparative_result = processor.process_order(comparative_config.order_id)
    print(f"🔍 Comparative order: {comparative_result['vehicles_found']} vehicles found")
    print(f"📊 Results saved to: {comparative_result['output_file']}")
    
    # Create a bulk order for specific dealerships (if we have multiple)
    dealerships = list(set([item['dealer_id'] for item in summary['top_make_models'][:5]]))
    if len(dealerships) > 0:
        bulk_config = OrderConfig(
            order_id=f"bulk_{timestamp}",
            order_type="bulk",
            dealerships=dealerships[:3],  # Top 3 dealerships
            filters={"batch_size": 500}
        )
        processor.create_order(bulk_config)
        bulk_result = processor.process_order(bulk_config.order_id)
        print(f"📦 Bulk order: {bulk_result['total_vehicles']} vehicles processed")
        print(f"📊 Results saved to: {bulk_result['output_file']}")
    
    print(f"\n🎉 Complete workflow finished!")
    print(f"📁 All results saved to: {output_dir}")
    
    return {
        'normalized_file': normalized_file,
        'import_result': import_result,
        'summary': summary,
        'comparative_result': comparative_result,
        'bulk_result': bulk_result if len(dealerships) > 0 else None
    }

def run_custom_order_demo():
    """
    Demonstrate custom order processing capabilities
    """
    print("🎯 Custom Order Processing Demo")
    print("=" * 50)
    
    processor = create_order_processor()
    
    # Demo: Search for specific vehicles
    print("\n🔍 Demo 1: Vehicle Search")
    search_results = processor.search_vehicles({
        'make': 'Honda',
        'price_range': (25000, 40000),
        'status': ['new', 'onlot'],
        'limit': 10
    })
    print(f"Found {len(search_results)} Honda vehicles between $25K-$40K")
    
    if len(search_results) > 0:
        print("Top results:")
        for _, row in search_results.head(3).iterrows():
            print(f"  • {row['year']} {row['make']} {row['model']} - ${row['price']:,} ({row['normalized_status']})")
    
    # Demo: Create list order with specific VINs
    if len(search_results) > 0:
        print(f"\n📝 Demo 2: List Order Processing")
        sample_vins = search_results['vin'].head(5).tolist()
        
        list_config = OrderConfig(
            order_id=f"demo_list_{datetime.now().strftime('%H%M%S')}",
            order_type="list",
            dealerships=[],
            filters={"vin_list": sample_vins}
        )
        
        processor.create_order(list_config)
        list_result = processor.process_order(list_config.order_id)
        print(f"📋 List order processed: {list_result['found_vehicles']}/{list_result['requested_vins']} VINs found")
        print(f"📊 Results: {list_result['output_file']}")
    
    print(f"\n✨ Custom order demo complete!")

def interactive_order_builder():
    """
    Interactive order builder for custom requirements
    """
    print("🛠️ Interactive Order Builder")
    print("=" * 40)
    
    processor = create_order_processor()
    
    # Get available dealerships
    summary = processor.get_dealership_inventory_summary()
    available_dealers = [item for item in summary['status_distribution']]
    
    print(f"\n📊 Database contains {summary['overall_stats']['total_vehicles']} vehicles")
    print(f"🏪 From {summary['overall_stats']['dealership_count']} dealerships")
    
    # Simple order type selection
    print(f"\n📋 Order Types:")
    print("1. List Order (specific VINs)")
    print("2. Comparative Order (compare across dealerships)")  
    print("3. Bulk Order (all inventory for dealerships)")
    
    choice = input("\nSelect order type (1-3): ").strip()
    
    timestamp = datetime.now().strftime('%H%M%S')
    
    if choice == "1":
        vins = input("Enter VINs (comma-separated): ").strip().split(',')
        vins = [v.strip().upper() for v in vins if v.strip()]
        
        if vins:
            config = OrderConfig(
                order_id=f"interactive_list_{timestamp}",
                order_type="list",
                dealerships=[],
                filters={"vin_list": vins}
            )
            
            processor.create_order(config)
            result = processor.process_order(config.order_id)
            print(f"\n✅ List order complete: {result['output_file']}")
    
    elif choice == "2":
        min_price = input("Minimum price (or press Enter): ").strip()
        max_price = input("Maximum price (or press Enter): ").strip()
        make = input("Make filter (or press Enter): ").strip()
        
        filters = {}
        if min_price.isdigit():
            filters['min_price'] = int(min_price)
        if max_price.isdigit():
            filters['max_price'] = int(max_price)
        if make:
            filters['make'] = make
        
        config = OrderConfig(
            order_id=f"interactive_comp_{timestamp}",
            order_type="comparative",
            dealerships=[],
            filters=filters
        )
        
        processor.create_order(config)
        result = processor.process_order(config.order_id)
        print(f"\n✅ Comparative order complete: {result['output_file']}")
    
    elif choice == "3":
        batch_size = input("Batch size (default 1000): ").strip()
        batch_size = int(batch_size) if batch_size.isdigit() else 1000
        
        config = OrderConfig(
            order_id=f"interactive_bulk_{timestamp}",
            order_type="bulk",
            dealerships=[],
            filters={"batch_size": batch_size}
        )
        
        processor.create_order(config)
        result = processor.process_order(config.order_id)
        print(f"\n✅ Bulk order complete: {result['output_file']}")
    
    else:
        print("❌ Invalid selection")

def main():
    """Main entry point with menu system"""
    print("🏁 Order Processing Control Center")
    print("Advanced order processing beyond Google Sheets limitations")
    print("=" * 65)
    
    while True:
        print(f"\n📋 Available Operations:")
        print("1. Complete Workflow (Raw CSV → Normalized → Orders)")
        print("2. Process Existing Normalized Data")
        print("3. Custom Order Demo")
        print("4. Interactive Order Builder")
        print("5. View Database Summary")
        print("0. Exit")
        
        choice = input("\nSelect operation (0-5): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            csv_file = input("Enter raw CSV file path (or press Enter to use existing): ").strip()
            if not csv_file:
                csv_file = None
            run_complete_workflow(csv_file)
        elif choice == "2":
            output_dir = "output_data"
            normalized_files = [f for f in os.listdir(output_dir) if f.startswith('normalized_') and f.endswith('.csv')]
            if normalized_files:
                latest_file = os.path.join(output_dir, sorted(normalized_files)[-1])
                print(f"Using: {latest_file}")
                run_complete_workflow(None, output_dir)
            else:
                print("❌ No normalized files found in output_data/")
        elif choice == "3":
            run_custom_order_demo()
        elif choice == "4":
            interactive_order_builder()
        elif choice == "5":
            processor = create_order_processor()
            summary = processor.get_dealership_inventory_summary()
            print(f"\n📊 Database Summary:")
            print(f"Total Vehicles: {summary['overall_stats']['total_vehicles']:,}")
            print(f"Dealerships: {summary['overall_stats']['dealership_count']}")
            print(f"Average Price: ${summary['overall_stats']['avg_price']:,.2f}")
            print(f"Price Range: ${summary['overall_stats']['min_price']:,} - ${summary['overall_stats']['max_price']:,}")
            
            print(f"\n📈 Status Distribution:")
            for status in summary['status_distribution']:
                print(f"  {status['normalized_status']}: {status['count']:,}")
        else:
            print("❌ Invalid selection")

if __name__ == "__main__":
    main()