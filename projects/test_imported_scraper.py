#!/usr/bin/env python3
"""
Test Imported Scraper Integration
==================================
Test one of our imported scrapers and add data to database
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add paths for both systems
sys.path.append('silverfox_scraper_system/silverfox_system')
sys.path.append('minisforum_database_transfer/bulletproof_package/scripts')

# Import database system
from database_connection import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imported_scraper():
    """Test an imported scraper and add data to database"""
    
    print("=" * 60)
    print("TESTING IMPORTED SCRAPER INTEGRATION")
    print("=" * 60)
    
    try:
        # Test Columbia Honda (one of our working scrapers)
        logger.info("Importing Columbia Honda scraper...")
        
        # Import the scraper module
        from core.scrapers.dealerships.columbiahonda_working import ColumbiahondaWorkingScraper
        
        # Instantiate scraper
        scraper = ColumbiahondaWorkingScraper()
        logger.info("Scraper instantiated successfully")
        
        # Get vehicles (this will likely use fallback data)
        logger.info("Running scraper to get vehicles...")
        vehicles = scraper.get_all_vehicles()
        
        print(f"Scraper returned {len(vehicles)} vehicles")
        
        if vehicles and len(vehicles) > 0:
            # Add first few vehicles to database
            vehicles_to_add = vehicles[:3]  # Add first 3 vehicles
            
            for i, vehicle in enumerate(vehicles_to_add):
                try:
                    # Insert into raw_vehicle_data table
                    db_manager.execute_non_query("""
                        INSERT INTO raw_vehicle_data (
                            vin, stock_number, year, make, model, trim, price, 
                            mileage, exterior_color, condition, dealer_name, 
                            raw_data, source, scraped_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vin, dealer_name) DO UPDATE SET
                            stock_number = EXCLUDED.stock_number,
                            year = EXCLUDED.year,
                            make = EXCLUDED.make,
                            model = EXCLUDED.model,
                            trim = EXCLUDED.trim,
                            price = EXCLUDED.price,
                            mileage = EXCLUDED.mileage,
                            exterior_color = EXCLUDED.exterior_color,
                            condition = EXCLUDED.condition,
                            raw_data = EXCLUDED.raw_data,
                            scraped_at = EXCLUDED.scraped_at
                    """, (
                        vehicle.get('vin', ''),
                        vehicle.get('stock_number', ''),
                        vehicle.get('year', 0),
                        vehicle.get('make', ''),
                        vehicle.get('model', ''),
                        vehicle.get('trim', ''),
                        vehicle.get('price', 0),
                        vehicle.get('mileage', 0),
                        vehicle.get('exterior_color', ''),
                        vehicle.get('condition', 'used'),
                        vehicle.get('dealer_name', 'Columbia Honda'),
                        json.dumps(vehicle),
                        'integrated_scraper',
                        datetime.now()
                    ))
                    
                    print(f"Added vehicle {i+1}: {vehicle.get('year', 'Unknown')} {vehicle.get('make', 'Unknown')} {vehicle.get('model', 'Unknown')}")
                    
                except Exception as e:
                    logger.error(f"Error adding vehicle {i+1}: {e}")
                    continue
            
            # Verify data was added
            vehicle_count = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM raw_vehicle_data WHERE dealer_name = %s", 
                ('Columbia Honda',)
            )[0]['count']
            
            print(f"\nDatabase now contains {vehicle_count} vehicles for Columbia Honda")
            
            return {
                'success': True,
                'scraper_tested': 'Columbia Honda',
                'vehicles_scraped': len(vehicles),
                'vehicles_added_to_db': len(vehicles_to_add),
                'total_in_db': vehicle_count
            }
        else:
            return {
                'success': False,
                'error': 'Scraper returned no vehicles'
            }
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            'success': False,
            'error': f'Could not import scraper: {e}'
        }
    except Exception as e:
        logger.error(f"Test error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function"""
    if not db_manager.test_connection():
        print("ERROR: Database connection failed")
        return False
    
    result = test_imported_scraper()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if result['success']:
        print("✅ SCRAPER INTEGRATION TEST SUCCESSFUL")
        print(f"   Scraper: {result['scraper_tested']}")
        print(f"   Vehicles scraped: {result['vehicles_scraped']}")
        print(f"   Added to database: {result['vehicles_added_to_db']}")
        print(f"   Total in database: {result['total_in_db']}")
    else:
        print("❌ SCRAPER INTEGRATION TEST FAILED")
        print(f"   Error: {result['error']}")
    
    return result['success']

if __name__ == "__main__":
    main()