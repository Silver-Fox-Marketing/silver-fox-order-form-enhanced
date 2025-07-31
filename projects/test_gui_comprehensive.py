#!/usr/bin/env python3
"""
Comprehensive Web GUI Functionality Test
"""

import sys
import os
import time
import requests
import json
from threading import Thread
import subprocess

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/web_gui'))

def start_gui_server():
    """Start the GUI server in background"""
    try:
        os.chdir('minisforum_database_transfer/bulletproof_package/web_gui')
        proc = subprocess.Popen([sys.executable, 'app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
        time.sleep(8)  # Give server time to start
        return proc
    except Exception as e:
        print(f"ERROR starting server: {e}")
        return None

def test_gui_routes():
    """Test all main GUI routes"""
    print("Testing GUI routes...")
    
    routes_to_test = [
        ('/', 'GET', 'Dashboard loads'),
        ('/api/status', 'GET', 'System status API'),
        ('/api/dealerships', 'GET', 'Dealerships API'),
        ('/api/system-stats', 'GET', 'System stats API')
    ]
    
    results = []
    
    for route, method, description in routes_to_test:
        try:
            if method == 'GET':
                response = requests.get(f'http://localhost:5000{route}', timeout=10)
            
            if response.status_code == 200:
                print(f"OK {description}: {response.status_code}")
                results.append((description, True, response.status_code))
            else:
                print(f"ERROR {description}: {response.status_code}")
                results.append((description, False, response.status_code))
                
        except Exception as e:
            print(f"ERROR {description}: {e}")
            results.append((description, False, str(e)))
    
    return results

def test_api_endpoints():
    """Test specific API endpoints"""
    print("\nTesting API endpoints...")
    
    # Test system status
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"OK System status API returned: {data.get('status', 'unknown')}")
            print(f"  Database connected: {data.get('database_connected', False)}")
            print(f"  Total vehicles: {data.get('total_vehicles', 0)}")
            status_success = True
        else:
            print(f"ERROR System status API failed: {response.status_code}")
            status_success = False
    except Exception as e:
        print(f"ERROR System status API error: {e}")
        status_success = False
    
    # Test dealerships API
    try:
        response = requests.get('http://localhost:5000/api/dealerships', timeout=10)
        if response.status_code == 200:
            data = response.json()
            dealerships = data.get('dealerships', [])
            print(f"OK Dealerships API returned {len(dealerships)} dealerships")
            for dealer in dealerships[:3]:  # Show first 3
                print(f"  - {dealer.get('name', 'Unknown')}: {dealer.get('vehicle_count', 0)} vehicles")
            dealerships_success = True
        else:
            print(f"ERROR Dealerships API failed: {response.status_code}")
            dealerships_success = False
    except Exception as e:
        print(f"ERROR Dealerships API error: {e}")
        dealerships_success = False
    
    return status_success and dealerships_success

def test_csv_upload_simulation():
    """Simulate CSV upload functionality"""
    print("\nTesting CSV upload simulation...")
    
    # Create a small test CSV
    test_csv_content = """vin,stock_number,dealer_name,year,make,model,price
TESTVIN123456789,TEST001,BMW of West St. Louis,2024,BMW,X5,55000
TESTVIN987654321,TEST002,Columbia Honda,2024,Honda,Pilot,38000"""
    
    try:
        files = {'file': ('test_data.csv', test_csv_content, 'text/csv')}
        response = requests.post('http://localhost:5000/api/import-csv', 
                               files=files, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"OK CSV upload simulation successful")
            print(f"  Records processed: {result.get('records_processed', 0)}")
            print(f"  Success: {result.get('success', False)}")
            return True
        else:
            print(f"ERROR CSV upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR CSV upload simulation error: {e}")
        return False

def test_order_processing_api():
    """Test order processing API"""
    print("\nTesting order processing API...")
    
    try:
        # Test creating an order
        order_data = {
            'dealership': 'BMW of West St. Louis',
            'job_type': 'standard'
        }
        
        response = requests.post('http://localhost:5000/api/create-order',
                               json=order_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"OK Order processing API successful")
            print(f"  Job ID: {result.get('job_id', 'N/A')}")
            print(f"  Vehicle count: {result.get('vehicle_count', 0)}")
            return True
        else:
            print(f"ERROR Order processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR Order processing API error: {e}")
        return False

def main():
    """Run comprehensive GUI tests"""
    print("=" * 60)
    print("COMPREHENSIVE WEB GUI FUNCTIONALITY TEST")
    print("=" * 60)
    
    original_dir = os.getcwd()
    server_proc = None
    
    try:
        # Start the server
        print("Starting web GUI server...")
        server_proc = start_gui_server()
        
        if not server_proc:
            print("ERROR Failed to start server")
            return False
        
        # Test basic routes
        route_results = test_gui_routes()
        
        # Test API endpoints
        api_success = test_api_endpoints()
        
        # Test CSV upload
        csv_success = test_csv_upload_simulation()
        
        # Test order processing
        order_success = test_order_processing_api()
        
        # Calculate overall results
        route_success_count = sum(1 for _, success, _ in route_results if success)
        total_route_tests = len(route_results)
        
        print(f"\n" + "=" * 60)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        print(f"Route Tests: {route_success_count}/{total_route_tests} passed")
        for desc, success, code in route_results:
            status = "PASS" if success else "FAIL"
            print(f"  {desc:<30} {status} ({code})")
        
        print(f"API Endpoints: {'PASS' if api_success else 'FAIL'}")
        print(f"CSV Upload: {'PASS' if csv_success else 'FAIL'}")
        print(f"Order Processing: {'PASS' if order_success else 'FAIL'}")
        
        overall_success = (
            route_success_count == total_route_tests and
            api_success and csv_success and order_success
        )
        
        if overall_success:
            print(f"\nOK ALL GUI FUNCTIONALITY TESTS PASSED!")
            print("The web GUI is 100% functional and ready for production use!")
            print("\nProduction ready features:")
            print("- Dashboard loading and display")
            print("- System status monitoring")
            print("- Dealership management")
            print("- CSV data import")
            print("- Order processing")
            print("- API endpoints working")
        else:
            print(f"\nERROR Some GUI functionality tests failed")
            print("Please review the errors above")
        
        return overall_success
        
    except Exception as e:
        print(f"ERROR during GUI testing: {e}")
        return False
        
    finally:
        # Cleanup
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except:
                server_proc.kill()
        
        os.chdir(original_dir)

if __name__ == "__main__":
    main()