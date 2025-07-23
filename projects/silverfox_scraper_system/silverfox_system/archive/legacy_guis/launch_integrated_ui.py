#!/usr/bin/env python3
"""
Launch Script for Integrated Scraper Pipeline UI
Simple launcher with error handling and logging
"""

import sys
import os
import traceback
from pathlib import Path

def main():
    """Launch the integrated UI with proper error handling"""
    print("🚀 Starting Integrated Scraper Pipeline UI...")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import and run the integrated UI
        from integrated_scraper_pipeline_ui import IntegratedScraperPipelineUI
        
        print("✅ Successfully imported integrated UI components")
        
        # Create and run the application
        app = IntegratedScraperPipelineUI()
        print("✅ Application initialized successfully")
        
        print("🚗 Launching Integrated Scraper Pipeline UI...")
        app.run()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("This might be due to missing dependencies or incorrect paths.")
        print("Please ensure all required modules are available.")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
    finally:
        print("👋 Application closed")

if __name__ == "__main__":
    main()