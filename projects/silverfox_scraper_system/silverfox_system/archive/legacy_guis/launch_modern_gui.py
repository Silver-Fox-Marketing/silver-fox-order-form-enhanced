#!/usr/bin/env python3
"""
Launch script for the Modern Scraper GUI
Easy double-click launcher for both Mac and PC users
"""

import sys
import os
from pathlib import Path

# Add scraper directories to path
current_dir = Path(__file__).parent
scraper_dir = current_dir / "scraper"
ui_dir = scraper_dir / "ui"

sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(scraper_dir))
sys.path.insert(0, str(ui_dir))

def main():
    """Launch the modern GUI"""
    print("🚀 Launching Silverfox Assistant - Modern Scraper GUI...")
    print("📁 Working directory:", current_dir)
    
    try:
        # Import and run the modern GUI
        from scraper.ui.modern_scraper_gui import main as run_gui
        run_gui()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📋 Trying direct import...")
        try:
            # Try direct import
            import scraper.ui.modern_scraper_gui as gui
            gui.main()
        except Exception as e2:
            print(f"❌ Could not start GUI: {e2}")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure you're running this from the silverfox_assistant directory")
            print("2. Check that all required Python packages are installed")
            print("3. Try running: python -m scraper.ui.modern_scraper_gui")
            return False
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")