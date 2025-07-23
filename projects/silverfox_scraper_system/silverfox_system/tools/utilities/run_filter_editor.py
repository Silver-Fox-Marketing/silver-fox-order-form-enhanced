#!/usr/bin/env python3
"""
Launch the dealership filter editor UI.
This provides a graphical interface for editing conditional filtering rules
for each individual dealership scraper.
"""

import os
import sys

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    from scraper.ui.filter_editor import FilterEditorUI
    
    def main():
        """Launch the filter editor UI"""
        print("🎯 Launching Dealership Filter Editor...")
        print("📝 Use this interface to edit conditional filtering rules for each dealership")
        
        app = FilterEditorUI()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Failed to import filter editor: {str(e)}")
    print("💡 Make sure tkinter is installed: pip install tk")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to launch filter editor: {str(e)}")
    sys.exit(1)