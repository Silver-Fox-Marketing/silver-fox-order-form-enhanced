#!/usr/bin/env python3
"""
Test script to verify Order Wizard fixes work correctly
"""
import requests
import json
import time

# Test the Flask app endpoint
base_url = "http://127.0.0.1:5000"

def test_cao_processing():
    """Test CAO order processing returns proper data structure"""
    print("Testing CAO order processing...")
    
    url = f"{base_url}/api/orders/process-cao"
    data = {
        "dealerships": ["Columbia Honda"],
        "vehicle_types": ["new", "cpo", "used"]
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response structure:")
            print(json.dumps(result, indent=2))
            
            # Check if result has expected fields
            if isinstance(result, list):
                result = result[0]
            
            expected_fields = ['success', 'dealership', 'new_vehicles', 'download_csv', 'qr_codes_generated']
            missing_fields = [field for field in expected_fields if field not in result]
            
            if missing_fields:
                print(f"Missing fields: {missing_fields}")
            else:
                print("All expected fields present")
                print(f"New vehicles: {result.get('new_vehicles', 0)}")
                print(f"QR codes generated: {result.get('qr_codes_generated', 0)}")
                
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error testing CAO processing: {e}")

def test_web_interface_access():
    """Test if web interface is accessible"""
    print("\nTesting web interface access...")
    
    try:
        response = requests.get(f"{base_url}/order_wizard", timeout=10)
        print(f"Order Wizard page status: {response.status_code}")
        
        if response.status_code == 200:
            print("Order Wizard page accessible")
            
            # Check if the page contains our v2.0 indicators
            content = response.text
            if "Order Processing Wizard v2.0" in content:
                print("Version 2.0 detected")
            if "showDataEditor" in content:
                print("Manual data editor code present")
            if "dataEditorStep" in content:
                print("Data editor step element present")
        else:
            print(f"Error accessing order wizard: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing web interface: {e}")

if __name__ == "__main__":
    print("Testing Order Wizard fixes...")
    print("=" * 50)
    
    # Test if Flask app is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"Flask app is running (status: {response.status_code})")
    except:
        print("Flask app is not running. Please start it first.")
        exit(1)
    
    test_web_interface_access()
    test_cao_processing()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("If all tests pass, the Order Wizard should now:")
    print("1. Process CAO orders and return proper data structure")
    print("2. Store results in processedOrders array")
    print("3. Show review step with 'Needs Editing' button")
    print("4. Allow access to manual data editor")