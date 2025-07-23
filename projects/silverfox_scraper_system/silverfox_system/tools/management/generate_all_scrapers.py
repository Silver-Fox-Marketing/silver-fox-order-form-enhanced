#!/usr/bin/env python3
"""
Generate updated scrapers for all dealerships while preserving original filtering logic.
This script analyzes the original scrapers and creates improved versions with better
error handling, rate limiting, and a modern architecture.
"""

import os
import sys
import logging
from datetime import datetime

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.scraper_generator import ScraperGenerator
from scraper.utils import setup_logging

def main():
    """Main function to generate all scrapers"""
    
    # Setup logging
    logger = setup_logging("INFO", "logs/scraper_generation.log")
    logger.info("Starting scraper generation process")
    
    try:
        # Initialize scraper generator
        generator = ScraperGenerator()
        
        print("🚀 Starting dealership scraper generation...")
        print(f"📊 Found {len(generator.dealership_files)} dealerships to process")
        
        # Generate all scrapers
        results = generator.generate_all_scrapers()
        
        # Report results
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        print(f"\n✅ Generation Complete!")
        print(f"✓ Successfully generated: {successful} scrapers")
        print(f"✗ Failed to generate: {failed} scrapers")
        
        if failed > 0:
            print(f"\n❌ Failed scrapers:")
            for filename, success in results.items():
                if not success:
                    print(f"   - {filename}")
        
        # Show successful scrapers
        print(f"\n✅ Successfully generated scrapers:")
        for filename, success in results.items():
            if success:
                dealership_id = filename.replace('.py', '')
                print(f"   ✓ {dealership_id}")
        
        print(f"\n📁 Generated files saved in: scraper/dealerships/")
        print(f"⚙️  Configuration files saved in: dealership_configs/")
        print(f"📋 Logs saved in: logs/")
        
        logger.info(f"Generation complete: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Scraper generation failed: {str(e)}")
        print(f"❌ Generation failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)