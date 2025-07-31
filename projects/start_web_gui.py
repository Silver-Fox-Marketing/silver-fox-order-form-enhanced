#!/usr/bin/env python3
"""
Start the Web GUI without Unicode issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/web_gui'))

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.chdir('minisforum_database_transfer/bulletproof_package/web_gui')

# Import and run the app
try:
    from app import app, socketio
    print("Starting web GUI server...")
    print("Open your browser to: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
except Exception as e:
    print(f"Error starting web GUI: {e}")
    import traceback
    traceback.print_exc()