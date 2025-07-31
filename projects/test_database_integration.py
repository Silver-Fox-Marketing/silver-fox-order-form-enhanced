#!/usr/bin/env python3
"""
Test Database Integration for Silver Fox System
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add paths for the database system
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
from order_processing_integration import OrderProcessingIntegrator
from qr_code_generator import QRCodeGenerator

def test_database_connection():
    """Test basic database connectivity"""
    print("Testing database connection...")
    
    if db_manager.test_connection():
        print("OK Database connected successfully")
        
        # Get table stats
        tables = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"OK Found {len(tables)} tables: {', '.join([t['table_name'] for t in tables])}")
        return True
    else:
        print("ERROR Database connection failed")
        return False

def test_sample_data_import():
    """Import some sample vehicle data to test the system"""
    print("\nTesting sample data import...")
    
    # Sample vehicle data
    sample_vehicles = [
        {
            'vin': '1HGCM82633A123456',
            'stock': 'T24001',
            'year': 2024,
            'make': 'Honda',
            'model': 'Accord',
            'trim': 'EX-L',
            'price': 32500.00,
            'msrp': 34500.00,
            'status': 'New',
            'condition': 'new',
            'dealership': 'Columbia Honda'
        },
        {
            'vin': '1FMCU0GD5KUA12345',
            'stock': 'F24002', 
            'year': 2024,
            'make': 'Ford',
            'model': 'Escape',
            'trim': 'Titanium',
            'price': 28900.00,
            'msrp': 31200.00,
            'status': 'New',
            'condition': 'new',
            'dealership': 'Suntrup Ford West'
        },
        {
            'vin': 'WBAJA7C50KC123456',
            'stock': 'B24003',
            'year': 2024,
            'make': 'BMW',
            'model': 'X3',
            'trim': 'xDrive30i',
            'price': 45200.00,
            'msrp': 47800.00,
            'status': 'New',
            'condition': 'new',
            'dealership': 'BMW of West St. Louis'
        }
    ]
    
    try:
        # Import to raw_vehicle_data
        raw_data = []
        for vehicle in sample_vehicles:
            raw_data.append((
                vehicle['vin'],
                vehicle['stock'],
                'New',
                vehicle['year'],
                vehicle['make'],
                vehicle['model'],
                vehicle['trim'],
                None,  # ext_color
                vehicle['status'],
                vehicle['price'],
                None,  # body_style
                None,  # fuel_type
                vehicle['msrp'],
                None,  # date_in_stock
                None,  # street_address
                None,  # locality
                None,  # postal_code
                None,  # region
                None,  # country
                vehicle['dealership'],
                None   # vehicle_url
            ))
        
        raw_count = db_manager.execute_batch_insert(
            'raw_vehicle_data',
            ['vin', 'stock', 'type', 'year', 'make', 'model', 'trim', 
             'ext_color', 'status', 'price', 'body_style', 'fuel_type',
             'msrp', 'date_in_stock', 'street_address', 'locality',
             'postal_code', 'region', 'country', 'location', 'vehicle_url'],
            raw_data
        )
        
        # Import to normalized_vehicle_data
        normalized_data = []
        for vehicle in sample_vehicles:
            normalized_data.append((
                vehicle['vin'],
                vehicle['stock'],
                vehicle['condition'],
                vehicle['year'],
                vehicle['make'],
                vehicle['model'],
                vehicle['trim'],
                vehicle['status'],
                vehicle['price'],
                vehicle['msrp'],
                None,  # date_in_stock
                vehicle['dealership'],
                None   # vehicle_url
            ))
        
        norm_count = db_manager.upsert_data(
            'normalized_vehicle_data',
            ['vin', 'stock', 'vehicle_condition', 'year', 'make', 'model',
             'trim', 'status', 'price', 'msrp', 'date_in_stock', 
             'location', 'vehicle_url'],
            normalized_data,
            conflict_columns=['vin', 'location']
        )
        
        print(f"OK Imported {raw_count} raw records and {norm_count} normalized records")
        return True
        
    except Exception as e:
        print(f"ERROR Sample data import failed: {e}")
        return False

def test_order_processing():
    """Test the order processing system"""
    print("\nTesting order processing...")
    
    try:
        integrator = OrderProcessingIntegrator()
        
        # Test with BMW dealership
        result = integrator.create_order_processing_job(
            "BMW of West St. Louis",
            "standard"
        )
        
        if result.get('success'):
            print(f"OK Order processing job created successfully")
            print(f"  - Job ID: {result.get('job_id')}")
            print(f"  - Vehicles found: {result.get('vehicle_count', 0)}")
            print(f"  - Export file: {result.get('export_file')}")
            return True
        else:
            print(f"ERROR Order processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"ERROR Order processing test failed: {e}")
        return False

def test_qr_generation():
    """Test QR code generation"""
    print("\nTesting QR code generation...")
    
    try:
        qr_generator = QRCodeGenerator(db_manager)
        
        # Test QR generation for sample VIN
        result = qr_generator.generate_qr_code(
            "1HGCM82633A123456",
            "T24001",
            "Columbia Honda"
        )
        
        if result.get('success'):
            print(f"OK QR code generated successfully")
            print(f"  - File path: {result.get('qr_file_path')}")
            return True
        else:
            print(f"ERROR QR generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"ERROR QR generation test failed: {e}")
        return False

def test_system_status():
    """Test system status reporting"""
    print("\nTesting system status...")
    
    try:
        # Get vehicle counts by dealership
        stats = db_manager.execute_query("""
            SELECT 
                location,
                COUNT(*) as vehicle_count,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM normalized_vehicle_data 
            WHERE price IS NOT NULL
            GROUP BY location
            ORDER BY vehicle_count DESC
        """)
        
        print(f"OK System status retrieved successfully")
        print("  Current inventory by dealership:")
        for stat in stats:
            print(f"    - {stat['location']}: {stat['vehicle_count']} vehicles (avg: ${stat['avg_price']:.2f})")
        
        # Get total system stats
        total_stats = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_vehicles,
                COUNT(DISTINCT location) as total_dealerships,
                AVG(price) as overall_avg_price
            FROM normalized_vehicle_data
            WHERE price IS NOT NULL
        """)[0]
        
        print(f"  Total: {total_stats['total_vehicles']} vehicles across {total_stats['total_dealerships']} dealerships")
        print(f"  Overall average price: ${total_stats['overall_avg_price']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"ERROR System status test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("SILVER FOX DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Sample Data Import", test_sample_data_import),
        ("Order Processing", test_order_processing),
        ("QR Code Generation", test_qr_generation),
        ("System Status", test_system_status)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nOK ALL TESTS PASSED - System is ready for production!")
        print("\nNext steps:")
        print("1. Access web GUI at: http://localhost:5000")
        print("2. Import your complete_data.csv files")
        print("3. Generate QR codes for dealerships")
        print("4. Export data for Adobe workflows")
    else:
        print(f"\nERROR {total - passed} tests failed - Please review errors above")
    
    return passed == total

if __name__ == "__main__":
    main()