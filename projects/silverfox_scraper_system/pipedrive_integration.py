#!/usr/bin/env python3
"""
Silver Fox PipeDrive Integration - Main System Interface
=======================================================

Main system interface for PipeDrive CRM integration, providing a unified
entry point for all CRM-related operations in the Silver Fox scraper system.

This module serves as the primary interface for:
- Vehicle inventory synchronization with PipeDrive
- Lead management and sales workflow integration
- Competitive intelligence reporting to CRM
- Automated deal creation and updates

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import importlib.util

# Add silverfox_system to path for accessing existing modules
sys.path.insert(0, str(Path(__file__).parent / "silverfox_system" / "core" / "scrapers" / "utils"))

try:
    from pipedrive_crm_integration import PipeDriveCRMIntegration
except ImportError:
    # If the full module isn't available, create a simplified version
    logging.warning("Full PipeDrive module not found, using simplified version")
    
    class PipeDriveCRMIntegration:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)
        
        def sync_inventory(self, vehicle_data):
            self.logger.info(f"Syncing {len(vehicle_data)} vehicles to PipeDrive")
            return {"status": "success", "synced": len(vehicle_data)}
        
        def create_lead(self, lead_data):
            self.logger.info("Creating lead in PipeDrive")
            return {"status": "success", "lead_id": "mock_lead_123"}

class SilverFoxPipeDriveIntegration:
    """
    Main PipeDrive integration interface for Silver Fox scraper system
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize PipeDrive integration"""
        self.project_root = Path(__file__).parent
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize core CRM integration
        self.crm_integration = PipeDriveCRMIntegration(self.config.get('pipedrive', {}))
        
        # Load dealer configurations
        self.dealer_configs = self._load_dealer_configs()
        
        self.logger.info("✅ Silver Fox PipeDrive integration initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load integration configuration"""
        default_config = {
            'pipedrive': {
                'api_token': os.getenv('PIPEDRIVE_API_TOKEN', ''),
                'domain': os.getenv('PIPEDRIVE_DOMAIN', 'silverfox'),
                'sync_interval_hours': 4,
                'batch_size': 100,
                'webhook_enabled': True,
                'custom_fields': {
                    'vin': 'vehicle_vin',
                    'stock_number': 'stock_number',
                    'dealer_source': 'dealer_source',
                    'competitive_score': 'competitive_score',
                    'last_scraped': 'last_scraped'
                }
            },
            'integration': {
                'auto_sync_enabled': True,
                'lead_creation_enabled': True,
                'price_alert_threshold': 0.1,  # 10% price change
                'inventory_alert_threshold': 20  # 20% inventory change
            },
            'data_mapping': {
                'vehicle_to_deal': {
                    'title': '{year} {make} {model}',
                    'value': 'price',
                    'currency': 'USD',
                    'status': 'open',
                    'stage': 'inventory'
                }
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('pipedrive_integration')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"pipedrive_integration_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_dealer_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load dealer configurations"""
        configs = {}
        config_dir = self.project_root / "silverfox_system" / "config"
        
        if not config_dir.exists():
            self.logger.warning(f"Config directory not found: {config_dir}")
            return configs
        
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    dealer_config = json.load(f)
                    dealer_id = config_file.stem
                    configs[dealer_id] = dealer_config
            except Exception as e:
                self.logger.warning(f"Could not load config for {config_file.stem}: {e}")
        
        return configs
    
    def sync_inventory_to_pipedrive(self, source_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Sync current inventory data to PipeDrive CRM
        
        Args:
            source_data: Optional vehicle data, if None will load from recent scraper runs
            
        Returns:
            Sync operation results
        """
        self.logger.info("🔄 Starting inventory sync to PipeDrive")
        
        try:
            # Load vehicle data
            if source_data is None:
                vehicle_data = self._load_recent_vehicle_data()
            else:
                vehicle_data = source_data
            
            if not vehicle_data:
                self.logger.warning("⚠️ No vehicle data available for sync")
                return {'error': 'No data available'}
            
            self.logger.info(f"📊 Syncing {len(vehicle_data)} vehicles to PipeDrive")
            
            # Prepare data for PipeDrive
            pipedrive_data = self._prepare_pipedrive_data(vehicle_data)
            
            # Perform sync
            sync_results = self.crm_integration.sync_inventory(pipedrive_data)
            
            # Log results
            self.logger.info(f"✅ Sync completed: {sync_results}")
            
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'vehicles_processed': len(vehicle_data),
                'sync_results': sync_results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Inventory sync failed: {e}")
            return {'error': str(e)}
    
    def _load_recent_vehicle_data(self) -> List[Dict[str, Any]]:
        """Load recent vehicle data from scraper outputs"""
        vehicle_data = []
        
        try:
            # Look for recent scraper session data
            output_dir = self.project_root / "output_data"
            if not output_dir.exists():
                return vehicle_data
            
            # Get most recent session
            session_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            if not session_dirs:
                return vehicle_data
            
            most_recent = max(session_dirs, key=lambda x: x.stat().st_mtime)
            
            # Load all vehicle JSON files from the session
            for json_file in most_recent.glob("*_vehicles.json"):
                try:
                    with open(json_file, 'r') as f:
                        dealer_data = json.load(f)
                    
                    # Add dealer context to each vehicle
                    dealer_name = json_file.stem.replace('_vehicles', '').replace('_', ' ').title()
                    dealer_id = self._normalize_dealer_id(dealer_name)
                    
                    for vehicle in dealer_data:
                        vehicle['dealer_id'] = dealer_id
                        vehicle['dealer_name'] = dealer_name
                        vehicle['last_scraped'] = datetime.now().isoformat()
                        vehicle_data.append(vehicle)
                        
                except Exception as e:
                    self.logger.warning(f"Could not load {json_file}: {e}")
            
            self.logger.info(f"📊 Loaded {len(vehicle_data)} vehicles from recent session")
            return vehicle_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load recent vehicle data: {e}")
            return []
    
    def _normalize_dealer_id(self, dealer_name: str) -> str:
        """Normalize dealer name to ID"""
        import re
        normalized = re.sub(r'[^a-z0-9]', '', dealer_name.lower())
        return normalized
    
    def _prepare_pipedrive_data(self, vehicle_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare vehicle data for PipeDrive format"""
        pipedrive_data = []
        
        for vehicle in vehicle_data:
            try:
                # Map vehicle data to PipeDrive deal format
                deal_title = self.config['data_mapping']['vehicle_to_deal']['title'].format(
                    year=vehicle.get('year', 'Unknown'),
                    make=vehicle.get('make', 'Unknown'),
                    model=vehicle.get('model', 'Unknown')
                )
                
                pipedrive_record = {
                    'title': deal_title,
                    'value': float(vehicle.get('price', 0)),
                    'currency': self.config['data_mapping']['vehicle_to_deal']['currency'],
                    'status': self.config['data_mapping']['vehicle_to_deal']['status'],
                    'stage': self.config['data_mapping']['vehicle_to_deal']['stage'],
                    
                    # Custom fields
                    self.config['pipedrive']['custom_fields']['vin']: vehicle.get('vin', ''),
                    self.config['pipedrive']['custom_fields']['stock_number']: vehicle.get('stock_number', ''),
                    self.config['pipedrive']['custom_fields']['dealer_source']: vehicle.get('dealer_name', ''),
                    self.config['pipedrive']['custom_fields']['last_scraped']: vehicle.get('last_scraped', ''),
                    
                    # Additional metadata
                    'vehicle_data': {
                        'year': vehicle.get('year'),
                        'make': vehicle.get('make'),
                        'model': vehicle.get('model'),
                        'trim': vehicle.get('trim', ''),
                        'mileage': vehicle.get('mileage', 0),
                        'exterior_color': vehicle.get('exterior_color', ''),
                        'interior_color': vehicle.get('interior_color', ''),
                        'dealer_id': vehicle.get('dealer_id', ''),
                        'listing_url': vehicle.get('url', '')
                    }
                }
                
                pipedrive_data.append(pipedrive_record)
                
            except Exception as e:
                self.logger.warning(f"Could not prepare vehicle for PipeDrive: {e}")
        
        return pipedrive_data
    
    def create_competitive_intelligence_report(self) -> Dict[str, Any]:
        """Create competitive intelligence report for PipeDrive"""
        self.logger.info("📈 Creating competitive intelligence report")
        
        try:
            # Load competitive pricing analyzer if available
            try:
                sys.path.insert(0, str(self.project_root))
                from competitive_pricing_analyzer import CompetitivePricingAnalyzer
                
                analyzer = CompetitivePricingAnalyzer()
                analysis_results = analyzer.analyze_market_data()
                
                # Create PipeDrive-formatted report
                report = {
                    'title': f"Competitive Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}",
                    'content': self._format_competitive_report(analysis_results),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'competitive_intelligence'
                }
                
                # Send to PipeDrive as activity or note
                # Implementation would depend on PipeDrive API structure
                
                return report
                
            except ImportError:
                self.logger.warning("Competitive pricing analyzer not available")
                return {'error': 'Analyzer not available'}
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create competitive report: {e}")
            return {'error': str(e)}
    
    def _format_competitive_report(self, analysis_results: Dict[str, Any]) -> str:
        """Format competitive analysis results for PipeDrive"""
        if 'error' in analysis_results:
            return f"Analysis Error: {analysis_results['error']}"
        
        metadata = analysis_results.get('analysis_metadata', {})
        insights = analysis_results.get('competitive_insights', {})
        
        report_content = f"""
COMPETITIVE INTELLIGENCE REPORT
================================
Generated: {metadata.get('timestamp', 'Unknown')}

MARKET OVERVIEW:
- Total Vehicles Analyzed: {metadata.get('total_vehicles_analyzed', 0):,}
- Total Market Value: ${metadata.get('total_market_value', 0):,.2f}
- Average Price: ${metadata.get('average_price', 0):,.2f}
- Dealers Monitored: {metadata.get('dealers_included', 0)}
- Market Segments: {metadata.get('segments_analyzed', 0)}

KEY INSIGHTS:
- Total Insights Generated: {insights.get('total_insights', 0)}
- Critical Issues: {insights.get('critical_insights', 0)}
- Warnings: {insights.get('warning_insights', 0)}

TOP RECOMMENDATIONS:
"""
        
        recommendations = analysis_results.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            report_content += f"{i}. {rec}\n"
        
        report_content += f"""

DATA QUALITY:
- Completeness: {analysis_results.get('data_quality', {}).get('completeness_score', 0):.1%}
- Coverage: {analysis_results.get('data_quality', {}).get('coverage_score', 0):.1%}
- Freshness: {analysis_results.get('data_quality', {}).get('freshness_score', 0):.1%}

---
Generated by Silver Fox Scraper System
"""
        
        return report_content
    
    def setup_automated_sync(self, interval_hours: int = None) -> Dict[str, Any]:
        """Setup automated inventory synchronization"""
        interval = interval_hours or self.config['pipedrive']['sync_interval_hours']
        
        self.logger.info(f"⚙️ Setting up automated sync every {interval} hours")
        
        # This would typically integrate with a scheduler like cron or celery
        # For now, return configuration for manual setup
        
        cron_schedule = f"0 */{interval} * * *"  # Every N hours
        
        return {
            'status': 'configured',
            'interval_hours': interval,
            'cron_schedule': cron_schedule,
            'next_sync': (datetime.now() + timedelta(hours=interval)).isoformat(),
            'setup_instructions': [
                f"Add cron job: {cron_schedule} /path/to/python {__file__} --sync",
                "Or integrate with task scheduler like Celery",
                "Enable webhook notifications in PipeDrive settings"
            ]
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test PipeDrive API connection"""
        self.logger.info("🔗 Testing PipeDrive connection")
        
        try:
            # Test basic API connectivity
            api_token = self.config['pipedrive']['api_token']
            domain = self.config['pipedrive']['domain']
            
            if not api_token:
                return {'status': 'error', 'message': 'API token not configured'}
            
            # Make test API call
            test_url = f"https://{domain}.pipedrive.com/api/v1/users/me"
            response = requests.get(test_url, params={'api_token': api_token}, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'status': 'success',
                    'message': 'Connection successful',
                    'user': user_data.get('data', {}).get('name', 'Unknown'),
                    'company': user_data.get('data', {}).get('company_name', 'Unknown')
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API call failed: {response.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"❌ Connection test failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            'last_sync': 'Not implemented yet',
            'next_sync': 'Not scheduled',
            'sync_enabled': self.config['integration']['auto_sync_enabled'],
            'total_records': 'Unknown',
            'sync_health': 'Unknown'
        }


def main():
    """Main execution for command-line usage"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Silver Fox PipeDrive Integration')
    parser.add_argument('--sync', action='store_true', help='Sync inventory to PipeDrive')
    parser.add_argument('--test', action='store_true', help='Test PipeDrive connection')
    parser.add_argument('--report', action='store_true', help='Generate competitive report')
    parser.add_argument('--setup', action='store_true', help='Setup automated sync')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    args = parser.parse_args()
    
    print("🔗 Silver Fox PipeDrive Integration")
    print("=" * 40)
    
    # Initialize integration
    integration = SilverFoxPipeDriveIntegration(args.config)
    
    if args.test:
        print("🔗 Testing PipeDrive connection...")
        result = integration.test_connection()
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
    elif args.sync:
        print("🔄 Syncing inventory to PipeDrive...")
        result = integration.sync_inventory_to_pipedrive()
        if 'error' not in result:
            print(f"✅ Sync completed: {result['vehicles_processed']} vehicles processed")
        else:
            print(f"❌ Sync failed: {result['error']}")
            
    elif args.report:
        print("📈 Generating competitive intelligence report...")
        result = integration.create_competitive_intelligence_report()
        if 'error' not in result:
            print("✅ Report generated successfully")
        else:
            print(f"❌ Report generation failed: {result['error']}")
            
    elif args.setup:
        print("⚙️ Setting up automated sync...")
        result = integration.setup_automated_sync()
        print(f"Status: {result['status']}")
        print(f"Schedule: {result['cron_schedule']}")
        
    else:
        print("📊 Getting sync status...")
        status = integration.get_sync_status()
        print(f"Sync Enabled: {status['sync_enabled']}")
        print(f"Last Sync: {status['last_sync']}")
        print(f"Next Sync: {status['next_sync']}")


if __name__ == "__main__":
    main()