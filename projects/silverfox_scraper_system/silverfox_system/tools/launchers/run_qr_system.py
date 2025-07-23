#!/usr/bin/env python3
"""
QR Code Management System
Complete QR generation, verification, and pre-print validation system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.qr_processor import QRProcessor, create_qr_processor, generate_qrs_for_order
from scraper.order_processor import create_order_processor
import schedule
import time
import threading
from datetime import datetime
import json

class QRSystemManager:
    """QR System management with scheduling and monitoring"""
    
    def __init__(self):
        self.qr_processor = create_qr_processor()
        self.order_processor = create_order_processor()
        self.scheduler_running = False
        self.scheduler_thread = None
    
    def start_scheduler(self):
        """Start the daily QR verification scheduler"""
        if self.scheduler_running:
            print("⚠️ Scheduler already running")
            return
        
        # Setup schedule
        schedule.every().day.at("06:00").do(self._daily_verification_job)
        
        def run_scheduler():
            self.scheduler_running = True
            print("🕐 QR Verification scheduler started (daily at 6:00 AM)")
            
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        schedule.clear()
        print("⏹️ QR Verification scheduler stopped")
    
    def _daily_verification_job(self):
        """Daily verification job"""
        print(f"🔍 Starting daily QR verification at {datetime.now()}")
        results = self.qr_processor.verify_all_qr_codes()
        print(f"✅ Daily verification complete: {results}")
    
    def generate_qrs_for_vehicles(self, vins_and_urls):
        """Generate QR codes for specific vehicles"""
        results = []
        
        for vin, url in vins_and_urls:
            try:
                qr_result = self.qr_processor.generate_qr_codes(vin, url)
                results.append(qr_result)
                print(f"✅ Generated QR codes for VIN: {vin}")
            except Exception as e:
                error_result = {'vin': vin, 'url': url, 'error': str(e)}
                results.append(error_result)
                print(f"❌ Failed to generate QR for VIN {vin}: {str(e)}")
        
        return results
    
    def run_pre_print_check(self):
        """Run pre-print validation check"""
        print("🔍 Running pre-print validation check...")
        
        report = self.qr_processor.get_pre_print_validation_report()
        
        print(f"\n📊 Pre-Print Validation Report")
        print("=" * 40)
        print(f"Print Safe: {'✅ YES' if report['print_safe'] else '❌ NO'}")
        print(f"Problematic QR Codes: {report['total_problematic_qrs']}")
        
        if report['total_problematic_qrs'] > 0:
            print(f"\n⚠️ Issues Found:")
            for vehicle in report['problematic_vehicles'][:10]:  # Show first 10
                print(f"  • VIN: {vehicle['vin']}")
                print(f"    Vehicle: {vehicle['vehicle_info']}")
                print(f"    Status: {vehicle['status']}")
                print(f"    URL: {vehicle['url']}")
                print("")
        
        if report['error_categories']:
            print(f"🏷️ Error Categories:")
            for error in report['error_categories']:
                print(f"  • {error['category']}: {error['count']} vehicles")
        
        return report
    
    def verify_specific_vins(self, vins):
        """Verify QR codes for specific VINs"""
        results = []
        
        for vin in vins:
            # Trigger verification for this VIN
            result = self.qr_processor.record_qr_scan(vin, 'manual_verification')
            if result:
                results.append(result)
                print(f"✅ Verified VIN {vin}: {result.status}")
            else:
                print(f"❌ No QR code found for VIN: {vin}")
        
        return results

def run_complete_qr_workflow():
    """Complete QR workflow demonstration"""
    print("🚀 Complete QR Code Workflow")
    print("=" * 50)
    
    qr_manager = QRSystemManager()
    
    # Step 1: Get some sample vehicles from database
    print("📊 Step 1: Getting sample vehicles from database")
    
    # Get recent vehicles with URLs
    import sqlite3
    with sqlite3.connect("data/order_processing.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vin, url FROM vehicles 
            WHERE url IS NOT NULL 
            LIMIT 5
        """)
        vehicles = cursor.fetchall()
    
    if not vehicles:
        print("❌ No vehicles with URLs found in database")
        print("💡 Please run the order processor first to import vehicle data")
        return
    
    print(f"Found {len(vehicles)} vehicles with URLs")
    
    # Step 2: Generate QR codes
    print("\n🎯 Step 2: Generating QR codes")
    qr_results = qr_manager.generate_qrs_for_vehicles(vehicles)
    successful_qrs = [r for r in qr_results if 'error' not in r]
    print(f"Generated {len(successful_qrs)} QR code pairs")
    
    # Step 3: Verify QR codes
    print("\n🔍 Step 3: Verifying QR codes")
    vins_to_verify = [r['vin'] for r in successful_qrs]
    verification_results = qr_manager.verify_specific_vins(vins_to_verify)
    
    # Step 4: Pre-print validation
    print("\n📋 Step 4: Pre-print validation check")
    validation_report = qr_manager.run_pre_print_check()
    
    # Step 5: Show statistics
    print("\n📈 Step 5: QR System Statistics")
    stats = qr_manager.qr_processor.get_verification_stats()
    print(f"Total QR Codes: {stats['total_qr_codes']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"Valid: {stats['valid_qrs']} | Invalid: {stats['invalid_qrs']} | Errors: {stats['error_qrs']}")
    
    return {
        'qr_results': qr_results,
        'verification_results': verification_results,
        'validation_report': validation_report,
        'stats': stats
    }

def interactive_qr_management():
    """Interactive QR management system"""
    print("🛠️ Interactive QR Management")
    print("=" * 40)
    
    qr_manager = QRSystemManager()
    
    while True:
        print(f"\n📋 QR Management Options:")
        print("1. Generate QR codes for VINs")
        print("2. Verify specific VIN QR codes")
        print("3. Run pre-print validation")
        print("4. View QR statistics")
        print("5. Start daily verification scheduler")
        print("6. Stop verification scheduler")
        print("7. Force verify all QR codes")
        print("8. Generate QRs for existing order")
        print("0. Exit")
        
        choice = input("\nSelect option (0-8): ").strip()
        
        if choice == "0":
            qr_manager.stop_scheduler()
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            print("Enter VIN and URL pairs (format: VIN,URL)")
            print("Enter empty line to finish:")
            
            vehicles = []
            while True:
                line = input("VIN,URL: ").strip()
                if not line:
                    break
                
                parts = line.split(',', 1)
                if len(parts) == 2:
                    vehicles.append((parts[0].strip(), parts[1].strip()))
                else:
                    print("❌ Invalid format. Use: VIN,URL")
            
            if vehicles:
                results = qr_manager.generate_qrs_for_vehicles(vehicles)
                print(f"✅ Generated QR codes for {len(results)} vehicles")
        
        elif choice == "2":
            vins = input("Enter VINs (comma-separated): ").strip().split(',')
            vins = [v.strip().upper() for v in vins if v.strip()]
            
            if vins:
                results = qr_manager.verify_specific_vins(vins)
                print(f"✅ Verified {len(results)} VINs")
        
        elif choice == "3":
            report = qr_manager.run_pre_print_check()
            
        elif choice == "4":
            stats = qr_manager.qr_processor.get_verification_stats()
            print(f"\n📊 QR Statistics:")
            print(f"Total QR Codes: {stats['total_qr_codes']:,}")
            print(f"Valid: {stats['valid_qrs']:,} ({stats['success_rate']:.1f}%)")
            print(f"Invalid: {stats['invalid_qrs']:,}")
            print(f"Errors: {stats['error_qrs']:,}")
            print(f"Pending: {stats['pending_qrs']:,}")
        
        elif choice == "5":
            qr_manager.start_scheduler()
        
        elif choice == "6":
            qr_manager.stop_scheduler()
        
        elif choice == "7":
            print("🔍 Starting verification of all QR codes...")
            results = qr_manager.qr_processor.verify_all_qr_codes(force_verify=True)
            print(f"✅ Verification complete: {results}")
        
        elif choice == "8":
            order_id = input("Enter Order ID: ").strip()
            if order_id:
                try:
                    results = generate_qrs_for_order(order_id)
                    if 'error' in results:
                        print(f"❌ {results['error']}")
                    else:
                        print(f"✅ Generated QRs for order {order_id}")
                        print(f"Successful: {results['successful_qrs']}/{results['total_vehicles']}")
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
        
        else:
            print("❌ Invalid selection")

def run_qr_scheduler_daemon():
    """Run QR verification scheduler as daemon process"""
    print("🕐 Starting QR Verification Daemon")
    print("This will run daily QR verification at 6:00 AM")
    print("Press Ctrl+C to stop")
    
    qr_manager = QRSystemManager()
    qr_manager.start_scheduler()
    
    try:
        while True:
            time.sleep(10)  # Keep main thread alive
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping QR verification daemon...")
        qr_manager.stop_scheduler()

def main():
    """Main entry point"""
    print("🎯 QR Code Management System")
    print("Advanced QR generation, verification, and validation")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "daemon":
            run_qr_scheduler_daemon()
            return
        elif sys.argv[1] == "workflow":
            run_complete_qr_workflow()
            return
        elif sys.argv[1] == "validate":
            qr_processor = create_qr_processor()
            report = qr_processor.get_pre_print_validation_report()
            print("Print Safe:" if report['print_safe'] else "❌ NOT PRINT SAFE")
            sys.exit(0 if report['print_safe'] else 1)
    
    while True:
        print(f"\n📋 QR System Operations:")
        print("1. Complete QR Workflow Demo")
        print("2. Interactive QR Management")
        print("3. Pre-Print Validation Only")
        print("4. Start Verification Daemon")
        print("0. Exit")
        
        choice = input("\nSelect operation (0-4): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            run_complete_qr_workflow()
        elif choice == "2":
            interactive_qr_management()
        elif choice == "3":
            qr_processor = create_qr_processor()
            report = qr_processor.get_pre_print_validation_report()
            if report['print_safe']:
                print("✅ All QR codes are valid - SAFE TO PRINT")
            else:
                print(f"❌ {report['total_problematic_qrs']} QR codes have issues - DO NOT PRINT")
        elif choice == "4":
            run_qr_scheduler_daemon()
        else:
            print("❌ Invalid selection")

if __name__ == "__main__":
    main()