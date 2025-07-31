#!/usr/bin/env python3
"""
Test Web GUI Loading
"""

import sys
import os
import time
import subprocess
import requests
from threading import Thread

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/web_gui'))

def test_gui_startup():
    """Test if the GUI starts successfully"""
    print("Testing web GUI startup...")
    
    try:
        # Change to GUI directory
        os.chdir('minisforum_database_transfer/bulletproof_package/web_gui')
        
        # Start the server in a subprocess
        proc = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give it time to start
        time.sleep(10)
        
        # Test if server is responding
        try:
            response = requests.get('http://localhost:5000', timeout=5)
            if response.status_code == 200:
                print("OK Web GUI started successfully and is responding")
                print(f"Status code: {response.status_code}")
                print(f"Content length: {len(response.content)} bytes")
                
                # Test if it contains expected elements
                content = response.text.lower()
                if 'dealership' in content or 'dashboard' in content or 'silver fox' in content:
                    print("OK GUI contains expected content")
                else:
                    print("WARNING GUI may not have loaded properly")
                
                result = True
            else:
                print(f"ERROR Server returned status code: {response.status_code}")
                result = False
                
        except requests.RequestException as e:
            print(f"ERROR Could not connect to web GUI: {e}")
            result = False
        
        # Clean up
        proc.terminate()
        proc.wait(timeout=5)
        
        return result
        
    except Exception as e:
        print(f"ERROR Failed to start web GUI: {e}")
        return False

def test_direct_import():
    """Test if we can import the app directly"""
    print("\nTesting direct import...")
    
    try:
        from app import app, socketio
        print("OK App imported successfully")
        
        # Test basic Flask app
        with app.test_client() as client:
            response = client.get('/')
            print(f"OK Test client returned status: {response.status_code}")
            
            if response.status_code == 200:
                print("OK Root route is working")
                return True
            else:
                print("ERROR Root route failed")
                return False
                
    except Exception as e:
        print(f"ERROR Direct import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run GUI tests"""
    print("=" * 50)
    print("WEB GUI TESTING")
    print("=" * 50)
    
    # Test direct import first
    import_success = test_direct_import()
    
    if import_success:
        # Test actual startup
        startup_success = test_gui_startup()
        
        if startup_success:
            print("\nOK All GUI tests passed!")
            print("Web GUI is ready for use at: http://localhost:5000")
            return True
        else:
            print("\nERROR GUI startup test failed")
            return False
    else:
        print("\nERROR GUI import test failed")
        return False

if __name__ == "__main__":
    original_dir = os.getcwd()
    try:
        main()
    finally:
        os.chdir(original_dir)