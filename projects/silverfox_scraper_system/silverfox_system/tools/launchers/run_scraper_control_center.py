#!/usr/bin/env python3
"""
Launch the Silverfox Scraper Control Center.
This provides a comprehensive GUI for managing and running all dealership scrapers
with individual filter controls and data normalization.
"""

import os
import sys

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    from scraper.ui.scraper_control_center import ScraperControlCenter
    
    def main():
        """Launch the Scraper Control Center"""
        print("🎯 Launching Silverfox Scraper Control Center...")
        print("🏪 Manage all 42+ dealership scrapers with individual filter controls")
        print("📊 Real-time scraping with data normalization pipeline")
        print("⚙️ Add new dealerships by URL analysis")
        
        app = ScraperControlCenter()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Failed to import Scraper Control Center: {str(e)}")
    print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to launch Scraper Control Center: {str(e)}")
    sys.exit(1)