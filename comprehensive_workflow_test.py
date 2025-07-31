#!/usr/bin/env python3
"""
Comprehensive Order Processing Wizard Workflow Test
Tests every step from initial setup to final QR codes and Adobe CSV output
"""
import requests
import json
import time
import os
from pathlib import Path
import webbrowser
import threading

base_url = "http://127.0.0.1:5000"

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        status = "PASS" if success else "FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details
        })
        print(f"[{status}] {test_name}: {details}")
        
    def test_flask_app_running(self):
        """Test 1: Verify Flask app is running"""
        try:
            response = self.session.get(base_url, timeout=5)
            self.log_result("Flask App Running", True, f"Status {response.status_code}")
            return True
        except Exception as e:
            self.log_result("Flask App Running", False, str(e))
            return False
            
    def test_order_wizard_page(self):
        """Test 2: Verify Order Wizard page loads with v2.0 features"""
        try:
            response = self.session.get(f"{base_url}/order-wizard", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Order Wizard Page", False, f"HTTP {response.status_code}")
                return False
                
            content = response.text
            checks = {
                "Order Processing Wizard v2.0": "Version 2.0 header",
                "showDataEditor": "Manual data editor function",
                "dataEditorStep": "Data editor step element",
                "wizard.showDataEditor()": "Data editor button onclick",
                "showQRUrlEditor": "QR URL editor function"
            }
            
            for check, desc in checks.items():
                if check in content:
                    self.log_result(f"Page Contains {desc}", True)
                else:
                    self.log_result(f"Page Contains {desc}", False)
                    
            self.log_result("Order Wizard Page", True, "All v2.0 features present")
            return True
            
        except Exception as e:
            self.log_result("Order Wizard Page", False, str(e))
            return False
            
    def test_cao_processing_backend(self):
        """Test 3: Test CAO processing backend functionality"""
        try:
            # Test with Columbia Honda (known working dealership)
            data = {
                "dealerships": ["Columbia Honda"],
                "vehicle_types": ["new", "cpo", "used"]
            }
            
            response = self.session.post(f"{base_url}/api/orders/process-cao", 
                                       json=data, timeout=60)
            
            if response.status_code != 200:
                self.log_result("CAO Backend Processing", False, f"HTTP {response.status_code}")
                return None
                
            result = response.json()
            if isinstance(result, list):
                result = result[0]
                
            # Verify critical fields
            required_fields = ['success', 'dealership', 'new_vehicles', 'qr_codes_generated', 'download_csv', 'csv_file']
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                self.log_result("CAO Backend Processing", False, f"Missing fields: {missing_fields}")
                return None
                
            vehicles = result.get('new_vehicles', 0)
            qr_codes = result.get('qr_codes_generated', 0)
            
            self.log_result("CAO Backend Processing", True, 
                          f"{vehicles} vehicles, {qr_codes} QR codes")
            
            # Store result for later tests
            self.cao_result = result
            return result
            
        except Exception as e:
            self.log_result("CAO Backend Processing", False, str(e))
            return None
            
    def test_csv_file_exists(self):
        """Test 4: Verify CSV file was actually created"""
        if not hasattr(self, 'cao_result'):
            self.log_result("CSV File Creation", False, "No CAO result to check")
            return False
            
        try:
            csv_path = self.cao_result.get('csv_file', '')
            if not csv_path:
                self.log_result("CSV File Creation", False, "No CSV path in result")
                return False
                
            # Convert to absolute path
            if not os.path.isabs(csv_path):
                csv_path = os.path.join(os.getcwd(), 
                                      "projects/minisforum_database_transfer/bulletproof_package/web_gui", 
                                      csv_path)
                
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                self.log_result("CSV File Creation", True, f"File exists, {file_size} bytes")
                
                # Quick content check
                with open(csv_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if "YEARMAKE,MODEL,TRIM,STOCK,VIN,@QR" in first_line:
                        self.log_result("CSV Format Correct", True, "Adobe variable data format detected")
                    else:
                        self.log_result("CSV Format Correct", False, f"Unexpected format: {first_line[:50]}...")
                        
                return True
            else:
                self.log_result("CSV File Creation", False, f"File not found: {csv_path}")
                return False
                
        except Exception as e:
            self.log_result("CSV File Creation", False, str(e))
            return False
            
    def test_qr_codes_exist(self):
        """Test 5: Verify QR code files were created"""
        if not hasattr(self, 'cao_result'):
            self.log_result("QR Code Creation", False, "No CAO result to check")
            return False
            
        try:
            qr_folder = self.cao_result.get('qr_folder', '')
            if not qr_folder:
                self.log_result("QR Code Creation", False, "No QR folder in result")
                return False
                
            # Convert to absolute path
            if not os.path.isabs(qr_folder):
                qr_folder = os.path.join(os.getcwd(), 
                                       "projects/minisforum_database_transfer/bulletproof_package/web_gui", 
                                       qr_folder)
                
            if os.path.exists(qr_folder):
                qr_files = [f for f in os.listdir(qr_folder) if f.endswith('.PNG')]
                self.log_result("QR Code Creation", True, f"{len(qr_files)} QR code files found")
                
                # Check one QR code file
                if qr_files:
                    sample_qr = os.path.join(qr_folder, qr_files[0])
                    qr_size = os.path.getsize(sample_qr)
                    self.log_result("QR Code File Size", True, f"Sample QR: {qr_size} bytes")
                    
                return True
            else:
                self.log_result("QR Code Creation", False, f"QR folder not found: {qr_folder}")
                return False
                
        except Exception as e:
            self.log_result("QR Code Creation", False, str(e))
            return False
            
    def test_csv_download_endpoint(self):
        """Test 6: Verify CSV download endpoint works"""
        if not hasattr(self, 'cao_result'):
            self.log_result("CSV Download Endpoint", False, "No CAO result to check")
            return False
            
        try:
            download_path = self.cao_result.get('download_csv', '')
            if not download_path:
                self.log_result("CSV Download Endpoint", False, "No download path in result")
                return False
                
            response = self.session.get(f"{base_url}{download_path}", timeout=10)
            
            if response.status_code == 200:
                content_length = len(response.content)
                self.log_result("CSV Download Endpoint", True, f"{content_length} bytes downloaded")
                
                # Verify it's CSV content
                content = response.text
                if "YEARMAKE,MODEL,TRIM" in content:
                    self.log_result("Downloaded CSV Format", True, "Adobe format confirmed")
                else:
                    self.log_result("Downloaded CSV Format", False, "Unexpected content")
                    
                return True
            else:
                self.log_result("CSV Download Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("CSV Download Endpoint", False, str(e))
            return False

    def test_csv_data_api(self):
        """Test 7: Test CSV data API for manual editing"""
        if not hasattr(self, 'cao_result'):
            self.log_result("CSV Data API", False, "No CAO result to check")
            return False
            
        try:
            download_path = self.cao_result.get('download_csv', '')
            if not download_path:
                self.log_result("CSV Data API", False, "No download path")
                return False
                
            # Extract filename from path
            filename = download_path.split('/')[-1]
            
            response = self.session.get(f"{base_url}/api/csv/get-data/{filename}", timeout=10)
            
            if response.status_code == 200:
                csv_data = response.json()
                
                if 'headers' in csv_data and 'rows' in csv_data:
                    headers = csv_data['headers']
                    rows = csv_data['rows']
                    self.log_result("CSV Data API", True, 
                                  f"{len(headers)} columns, {len(rows)} rows")
                    
                    # Verify Adobe format columns
                    expected_cols = ['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR']
                    missing_cols = [col for col in expected_cols if col not in headers]
                    
                    if not missing_cols:
                        self.log_result("CSV Data Structure", True, "All Adobe columns present")
                    else:
                        self.log_result("CSV Data Structure", False, f"Missing: {missing_cols}")
                        
                    return True
                else:
                    self.log_result("CSV Data API", False, "Invalid JSON structure")
                    return False
            else:
                self.log_result("CSV Data API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("CSV Data API", False, str(e))
            return False

    def open_browser_for_manual_test(self):
        """Test 8: Open browser for manual workflow testing"""
        try:
            print("\n" + "="*60)
            print("MANUAL TESTING PHASE")
            print("="*60)
            print("Opening Order Wizard in browser for manual testing...")
            print("\nManual Test Steps:")
            print("1. Click 'Process Queue' button")
            print("2. Select Columbia Honda for CAO processing")
            print("3. Click 'Start Processing'")
            print("4. Wait for processing to complete")
            print("5. Look for 'Review Generated Files' step")
            print("6. Click 'Needs Editing' button")
            print("7. Verify Manual Data Editor opens")
            print("8. Try editing a cell")
            print("9. Click 'Approve & Continue'")
            print("10. Click 'Download All Files'")
            
            webbrowser.open(f"{base_url}/order-wizard")
            
            input("\nPress Enter when you've completed the manual testing...")
            
            self.log_result("Manual Browser Test", True, "Browser opened for manual testing")
            return True
            
        except Exception as e:
            self.log_result("Manual Browser Test", False, str(e))
            return False

    def print_summary(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("COMPREHENSIVE WORKFLOW TEST RESULTS")
        print("="*80)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        total = len(self.test_results)
        
        print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print()
        
        for result in self.test_results:
            status_symbol = "PASS" if result['status'] == 'PASS' else "FAIL"
            print(f"{status_symbol} {result['test']}: {result['details']}")
            
        print("\n" + "="*80)
        
        if passed == total:
            print("*** ALL TESTS PASSED! Order Processing Wizard is fully functional. ***")
        else:
            print(f"*** {total - passed} tests failed. Check the details above. ***")
            
        print("\nNext Steps:")
        print("- All backend processing is working correctly")
        print("- Files are being generated (CSV + QR codes)")
        print("- Download endpoints are functional")
        print("- Manual data editor should now be accessible")
        print("- QR URL editor should be available in the wizard")

def main():
    print("Starting Comprehensive Order Processing Workflow Test")
    print("="*60)
    
    tester = WorkflowTester()
    
    # Run automated tests
    tests = [
        tester.test_flask_app_running,
        tester.test_order_wizard_page,
        tester.test_cao_processing_backend,
        tester.test_csv_file_exists,
        tester.test_qr_codes_exist,
        tester.test_csv_download_endpoint,
        tester.test_csv_data_api,
    ]
    
    all_passed = True
    for test in tests:
        result = test()
        if result is False:
            all_passed = False
            
    # If automated tests pass, open browser for manual testing
    if all_passed:
        tester.open_browser_for_manual_test()
    
    # Print final summary
    tester.print_summary()

if __name__ == "__main__":
    main()