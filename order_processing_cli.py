#!/usr/bin/env python3
"""
Silver Fox Order Processing CLI - Backup System
Command line interface for order processing when web interface is unavailable
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project paths
project_root = Path(__file__).parent / "projects" / "minisforum_database_transfer" / "bulletproof_package"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(scripts_path))

try:
    from correct_order_processing import CorrectOrderProcessor
    from database_connection import db_manager
except ImportError as e:
    print(f"❌ ERROR: Could not import required modules: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('order_processing_cli.log')
    ]
)
logger = logging.getLogger(__name__)

class OrderProcessingCLI:
    """Command line interface for order processing"""
    
    def __init__(self):
        self.processor = CorrectOrderProcessor()
        self.available_dealerships = [
            'BMW of West St. Louis',
            'Columbia Honda',
            'Dave Sinclair Lincoln South',
            'Test Integration Dealer'
        ]
        self.available_templates = ['shortcut', 'shortcut_pack', 'flyout']
        
    def list_dealerships(self):
        """List available dealerships"""
        print("\nAVAILABLE DEALERSHIPS:")
        print("=" * 50)
        for i, dealer in enumerate(self.available_dealerships, 1):
            print(f"{i}. {dealer}")
        print("=" * 50)
        
    def list_templates(self):
        """List available templates"""
        print("\nAVAILABLE TEMPLATES:")
        print("=" * 30)
        for i, template in enumerate(self.available_templates, 1):
            print(f"{i}. {template}")
        print("=" * 30)
    
    def check_system_status(self):
        """Check system status and connections"""
        print("\nSYSTEM STATUS CHECK")
        print("=" * 50)
        
        # Check database connection
        try:
            result = db_manager.execute_query("SELECT COUNT(*) as count FROM vin_history")
            vin_count = result[0]['count'] if result else 0
            print(f"[OK] Database: Connected ({vin_count:,} VINs in history)")
        except Exception as e:
            print(f"[ERROR] Database: Error - {e}")
            return False
        
        # Check VIN history
        try:
            result = db_manager.execute_query("""
                SELECT COUNT(DISTINCT dealership_name) as dealer_count
                FROM vin_history
            """)
            dealer_count = result[0]['dealer_count'] if result else 0
            print(f"[OK] VIN History: {dealer_count} dealerships tracked")
        except Exception as e:
            print(f"[ERROR] VIN History: Error - {e}")
        
        # Check vehicle data
        try:
            result = db_manager.execute_query("""
                SELECT location, COUNT(*) as vehicle_count
                FROM raw_vehicle_data
                GROUP BY location
                ORDER BY vehicle_count DESC
                LIMIT 5
            """)
            print("[OK] Vehicle Data:")
            for row in result:
                print(f"   {row['location']}: {row['vehicle_count']} vehicles")
        except Exception as e:
            print(f"[ERROR] Vehicle Data: Error - {e}")
        
        print("=" * 50)
        return True
    
    def process_cao_order(self, dealership: str, template: str = "shortcut_pack"):
        """Process a CAO (Comparative Analysis Order)"""
        print(f"\nPROCESSING CAO ORDER")
        print("=" * 50)
        print(f"Dealership: {dealership}")
        print(f"Template: {template}")
        print(f"Order Type: CAO (Compare Against Outstanding)")
        print("=" * 50)
        
        try:
            result = self.processor.process_cao_order(dealership, template)
            
            if result['success']:
                print("[SUCCESS] ORDER PROCESSED SUCCESSFULLY")
                print(f"   New vehicles: {result['new_vehicles']}")
                print(f"   QR codes generated: {result['qr_codes_generated']}")
                print(f"   CSV file: {result['csv_file']}")
                print(f"   QR folder: {result['qr_folder']}")
                print(f"   Timestamp: {result['timestamp']}")
                
                if result.get('total_vehicles'):
                    filtered = result['total_vehicles'] - result['new_vehicles']
                    print(f"   Total vehicles found: {result['total_vehicles']}")
                    print(f"   Filtered by VIN history: {filtered}")
                    if result['total_vehicles'] > 0:
                        print(f"   Filter efficiency: {filtered/result['total_vehicles']*100:.1f}%")
                
                return result
            else:
                print(f"[ERROR] ORDER PROCESSING FAILED: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"[ERROR] PROCESSING ERROR: {e}")
            logger.error(f"CAO processing error: {e}")
            return None
    
    def process_list_order(self, dealership: str, vin_list: List[str], template: str = "shortcut_pack"):
        """Process a LIST order with specific VINs"""
        print(f"\nPROCESSING LIST ORDER")
        print("=" * 50)
        print(f"Dealership: {dealership}")
        print(f"Template: {template}")
        print(f"Order Type: LIST (Specific VINs)")
        print(f"VIN Count: {len(vin_list)}")
        print("=" * 50)
        
        try:
            result = self.processor.process_list_order(dealership, vin_list, template)
            
            if result['success']:
                print("[SUCCESS] ORDER PROCESSED SUCCESSFULLY")
                print(f"   Vehicles processed: {result['vehicles_processed']}")
                print(f"   QR codes generated: {result['qr_codes_generated']}")
                print(f"   CSV file: {result['csv_file']}")
                print(f"   QR folder: {result['qr_folder']}")
                print(f"   Timestamp: {result['timestamp']}")
                return result
            else:
                print(f"[ERROR] ORDER PROCESSING FAILED: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"[ERROR] PROCESSING ERROR: {e}")
            logger.error(f"LIST processing error: {e}")
            return None
    
    def interactive_mode(self):
        """Interactive mode for order processing"""
        print("\nINTERACTIVE ORDER PROCESSING MODE")
        print("=" * 60)
        print("Type 'help' for commands, 'quit' to exit")
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif command == 'help':
                    self.show_help()
                
                elif command == 'status':
                    self.check_system_status()
                
                elif command == 'dealers':
                    self.list_dealerships()
                
                elif command == 'templates':
                    self.list_templates()
                
                elif command.startswith('cao'):
                    self.handle_cao_command(command)
                
                elif command.startswith('list'):
                    self.handle_list_command(command)
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"[ERROR] Error: {e}")
    
    def show_help(self):
        """Show help information"""
        print("\nAVAILABLE COMMANDS:")
        print("=" * 40)
        print("help      - Show this help")
        print("status    - Check system status")
        print("dealers   - List available dealerships")
        print("templates - List available templates")
        print("cao       - Process CAO order (interactive)")
        print("list      - Process LIST order (interactive)")
        print("quit      - Exit the program")
        print("=" * 40)
    
    def handle_cao_command(self, command):
        """Handle CAO command interactively"""
        print("\nCAO ORDER SETUP")
        print("-" * 30)
        
        # Select dealership
        self.list_dealerships()
        try:
            choice = int(input("Select dealership (number): ")) - 1
            if 0 <= choice < len(self.available_dealerships):
                dealership = self.available_dealerships[choice]
            else:
                print("[ERROR] Invalid dealership selection")
                return
        except ValueError:
            print("[ERROR] Please enter a valid number")
            return
        
        # Select template
        self.list_templates()
        try:
            choice = int(input("Select template (number): ")) - 1
            if 0 <= choice < len(self.available_templates):
                template = self.available_templates[choice]
            else:
                print("[ERROR] Invalid template selection")
                return
        except ValueError:
            print("[ERROR] Please enter a valid number")
            return
        
        # Process the order
        self.process_cao_order(dealership, template)
    
    def handle_list_command(self, command):
        """Handle LIST command interactively"""
        print("\nLIST ORDER SETUP")
        print("-" * 30)
        
        # Select dealership
        self.list_dealerships()
        try:
            choice = int(input("Select dealership (number): ")) - 1
            if 0 <= choice < len(self.available_dealerships):
                dealership = self.available_dealerships[choice]
            else:
                print("[ERROR] Invalid dealership selection")
                return
        except ValueError:
            print("[ERROR] Please enter a valid number")
            return
        
        # Get VIN list
        print("\nEnter VINs (one per line, empty line to finish):")
        vin_list = []
        while True:
            vin = input("VIN: ").strip()
            if not vin:
                break
            vin_list.append(vin)
        
        if not vin_list:
            print("[ERROR] No VINs entered")
            return
        
        # Select template
        self.list_templates()
        try:
            choice = int(input("Select template (number): ")) - 1
            if 0 <= choice < len(self.available_templates):
                template = self.available_templates[choice]
            else:
                print("[ERROR] Invalid template selection")
                return
        except ValueError:
            print("[ERROR] Please enter a valid number")
            return
        
        # Process the order
        self.process_list_order(dealership, vin_list, template)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Silver Fox Order Processing CLI - Backup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --status                                    # Check system status
  %(prog)s --dealers                                   # List dealerships
  %(prog)s --cao "Columbia Honda" --template shortcut_pack  # Process CAO order
  %(prog)s --list "BMW of West St. Louis" --vins vin1,vin2,vin3  # Process LIST order
  %(prog)s --interactive                               # Interactive mode
        """
    )
    
    parser.add_argument('--status', action='store_true', help='Check system status')
    parser.add_argument('--dealers', action='store_true', help='List available dealerships') 
    parser.add_argument('--templates', action='store_true', help='List available templates')
    parser.add_argument('--cao', metavar='DEALERSHIP', help='Process CAO order for dealership')
    parser.add_argument('--list', metavar='DEALERSHIP', help='Process LIST order for dealership')
    parser.add_argument('--template', default='shortcut_pack', help='Template to use (default: shortcut_pack)')
    parser.add_argument('--vins', help='Comma-separated list of VINs for LIST orders')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    
    args = parser.parse_args()
    
    # Print banner
    print("SILVER FOX ORDER PROCESSING CLI v2.0")
    print("=" * 60)
    print("Backup command line interface for order processing")
    print("Created: July 30, 2025")
    print("=" * 60)
    
    cli = OrderProcessingCLI()
    
    # Handle arguments
    if args.status:
        cli.check_system_status()
    
    elif args.dealers:
        cli.list_dealerships()
    
    elif args.templates:
        cli.list_templates()
    
    elif args.cao:
        if not cli.check_system_status():
            print("[ERROR] System check failed. Cannot process orders.")
            return 1
        
        result = cli.process_cao_order(args.cao, args.template)
        return 0 if result else 1
    
    elif args.list:
        if not args.vins:
            print("[ERROR] --vins required for LIST orders")
            return 1
        
        if not cli.check_system_status():
            print("[ERROR] System check failed. Cannot process orders.")
            return 1
        
        vin_list = [vin.strip() for vin in args.vins.split(',')]
        result = cli.process_list_order(args.list, vin_list, args.template)
        return 0 if result else 1
    
    elif args.interactive:
        if not cli.check_system_status():
            print("[ERROR] System check failed. Interactive mode may not work properly.")
        cli.interactive_mode()
    
    else:
        # No arguments provided, show help
        parser.print_help()
        print("\nTIP: Use --interactive for guided order processing")
        print("TIP: Use --status to check system health")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)