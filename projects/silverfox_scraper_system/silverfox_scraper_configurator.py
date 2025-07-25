#!/usr/bin/env python3
"""
Silver Fox Scraper Configurator
==============================

Configuration-driven scraper management system based on proven GitHub patterns.
Provides CSV-based orchestration for all 40 Silver Fox dealership scrapers.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import pandas as pd
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class SilverFoxScraperConfigurator:
    """Configuration management system for all 40 Silver Fox scrapers"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configurator with config directory"""
        self.project_root = Path(__file__).parent
        self.config_dir = Path(config_dir) if config_dir else self.project_root / "silverfox_system" / "config"
        self.csv_config_file = self.project_root / "scraper_config.csv"
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize CSV configuration if it doesn't exist
        if not self.csv_config_file.exists():
            self._create_initial_csv_config()
    
    def _create_initial_csv_config(self):
        """Create initial CSV configuration from JSON files"""
        self.logger.info("Creating initial CSV configuration from JSON files...")
        
        # Scan all JSON config files
        json_configs = []
        for json_file in self.config_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    config = json.load(f)
                
                # Extract key information for CSV
                csv_row = {
                    'site_name': config.get('name', json_file.stem),
                    'config_file': json_file.name,
                    'scraper_type': config.get('scraper_type', 'api'),
                    'base_url': config.get('base_url', ''),
                    'platform': config.get('api_platform', 'dealeron'),
                    'to_scrap': 'yes',  # Default to enabled following GitHub pattern
                    'priority': self._determine_priority(config),
                    'expected_vehicles': self._estimate_vehicles(config),
                    'scraper_class': self._determine_scraper_class(json_file.stem),
                    'last_updated': config.get('updated_at', datetime.now().isoformat()),
                    'status': 'configured'
                }
                json_configs.append(csv_row)
                
            except Exception as e:
                self.logger.warning(f"Could not process {json_file}: {e}")
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(json_configs)
        df = df.sort_values('site_name')  # Sort alphabetically
        df.to_csv(self.csv_config_file, index=False)
        
        self.logger.info(f"Created CSV configuration with {len(json_configs)} scrapers")
        return df
    
    def _determine_priority(self, config: Dict[str, Any]) -> str:
        """Determine scraper priority based on configuration"""
        name = config.get('name', '').lower()
        
        # High priority dealerships
        if any(brand in name for brand in ['bmw', 'jaguar', 'land rover', 'aston martin', 'bentley', 'mclaren', 'rolls-royce']):
            return 'high'
        
        # Medium priority dealerships  
        if any(brand in name for brand in ['ford', 'toyota', 'honda', 'hyundai']):
            return 'medium'
        
        return 'low'
    
    def _estimate_vehicles(self, config: Dict[str, Any]) -> int:
        """Estimate expected vehicle count based on dealership type"""
        name = config.get('name', '').lower()
        
        # Luxury brands typically have smaller inventories
        if any(brand in name for brand in ['rolls-royce', 'mclaren', 'aston martin']):
            return 5
        elif any(brand in name for brand in ['bentley', 'jaguar']):
            return 10
        elif 'land rover' in name:
            return 15
        elif 'bmw' in name:
            return 50
        elif any(brand in name for brand in ['ford', 'toyota', 'honda', 'hyundai']):
            return 40
        
        return 30  # Default estimate
    
    def _determine_scraper_class(self, config_id: str) -> str:
        """Determine appropriate scraper class name"""
        # Convert config filename to scraper class name
        class_name = ''.join(word.capitalize() for word in config_id.replace('_', ' ').split())
        return f"{class_name}WorkingScraper"
    
    def load_configuration(self) -> pd.DataFrame:
        """Load current CSV configuration"""
        if not self.csv_config_file.exists():
            return self._create_initial_csv_config()
        
        try:
            df = pd.read_csv(self.csv_config_file)
            return df.sort_values('site_name')
        except Exception as e:
            self.logger.error(f"Error loading CSV config: {e}")
            return self._create_initial_csv_config()
    
    def get_enabled_scrapers(self) -> pd.DataFrame:
        """Get only scrapers marked for execution"""
        df = self.load_configuration()
        return df[df['to_scrap'].str.lower() == 'yes'].copy()
    
    def get_scraper_config(self, site_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed JSON configuration for a specific scraper"""
        df = self.load_configuration()
        row = df[df['site_name'] == site_name]
        
        if row.empty:
            return None
        
        config_file = row.iloc[0]['config_file']
        config_path = self.config_dir / config_file
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config for {site_name}: {e}")
            return None
    
    def update_scraper_status(self, site_name: str, status: str, **kwargs):
        """Update scraper status in CSV configuration"""
        df = self.load_configuration()
        
        # Update the row
        mask = df['site_name'] == site_name
        if mask.any():
            df.loc[mask, 'status'] = status
            df.loc[mask, 'last_updated'] = datetime.now().isoformat()
            
            # Update any additional fields
            for key, value in kwargs.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            # Save back to CSV
            df.to_csv(self.csv_config_file, index=False)
            self.logger.info(f"Updated {site_name} status to {status}")
    
    def enable_scraper(self, site_name: str):
        """Enable a scraper for execution"""
        self.update_scraper_status(site_name, 'enabled', to_scrap='yes')
    
    def disable_scraper(self, site_name: str):
        """Disable a scraper from execution"""
        self.update_scraper_status(site_name, 'disabled', to_scrap='no')
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of scraper configuration"""
        df = self.load_configuration()
        
        stats = {
            'total_scrapers': len(df),
            'enabled_scrapers': len(df[df['to_scrap'].str.lower() == 'yes']),
            'disabled_scrapers': len(df[df['to_scrap'].str.lower() == 'no']),
            'by_platform': df['platform'].value_counts().to_dict(),
            'by_priority': df['priority'].value_counts().to_dict(),
            'estimated_total_vehicles': df['expected_vehicles'].sum(),
            'enabled_vehicles': df[df['to_scrap'].str.lower() == 'yes']['expected_vehicles'].sum()
        }
        
        return stats
    
    def export_for_main_script(self, output_file: str = None) -> str:
        """Export configuration in format compatible with main scraper script"""
        if not output_file:
            output_file = self.project_root / "main_scraper_config.csv"
        
        df = self.load_configuration()
        
        # Select and rename columns to match main.py expectations
        export_df = df[['site_name', 'to_scrap', 'scraper_class', 'priority']].copy()
        
        # Add any additional columns needed by main script
        export_df['scraper_module'] = export_df['scraper_class'].str.lower().str.replace('workingscraper', '_working')
        
        export_df.to_csv(output_file, index=False)
        self.logger.info(f"Exported configuration to {output_file}")
        
        return str(output_file)


def main():
    """Main entry point for configuration management"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    configurator = SilverFoxScraperConfigurator()
    
    print("🏗️ Silver Fox Scraper Configuration Manager")
    print("=" * 50)
    
    # Load and display configuration
    df = configurator.load_configuration()
    print(f"📊 Loaded {len(df)} scraper configurations")
    
    # Show summary stats
    stats = configurator.get_summary_stats()
    print(f"✅ Enabled: {stats['enabled_scrapers']}/{stats['total_scrapers']} scrapers")
    print(f"🚗 Expected vehicles: {stats['enabled_vehicles']} total")
    
    # Platform breakdown
    print("\\n🏭 Platform Distribution:")
    for platform, count in stats['by_platform'].items():
        print(f"   {platform}: {count} scrapers")
    
    # Export for main script
    export_file = configurator.export_for_main_script()
    print(f"\\n📋 Configuration exported to: {export_file}")
    
    print("\\n🎯 Ready for scraper execution!")


if __name__ == "__main__":
    main()